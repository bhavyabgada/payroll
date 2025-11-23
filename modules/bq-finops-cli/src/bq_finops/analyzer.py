"""Cost analysis for BigQuery."""

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud.bigquery import Client

from bq_finops.config import AnalysisConfig, CostReport


class CostAnalyzer:
    """Analyze BigQuery costs and usage patterns.
    
    This class provides methods to:
    - Analyze query costs over time periods
    - Identify expensive queries
    - Break down costs by dataset, user, table
    - Generate cost optimization recommendations
    
    Attributes:
        client: BigQuery client
        project_id: GCP project ID
    """
    
    # BigQuery pricing: $6.25 per TB processed (on-demand)
    COST_PER_TB = 6.25
    BYTES_PER_TB = 1024 ** 4
    
    def __init__(self, project_id: str, client: Optional[Client] = None):
        """Initialize cost analyzer.
        
        Args:
            project_id: GCP project ID
            client: Optional BigQuery client (creates new if None)
        """
        self.project_id = project_id
        self.client = client or bigquery.Client(project=project_id)
    
    def calculate_query_cost(self, bytes_processed: int) -> float:
        """Calculate cost for bytes processed.
        
        Args:
            bytes_processed: Number of bytes processed
        
        Returns:
            Cost in USD
        """
        tb_processed = bytes_processed / self.BYTES_PER_TB
        return tb_processed * self.COST_PER_TB
    
    def analyze_period(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        datasets: Optional[List[str]] = None
    ) -> CostReport:
        """Analyze costs for a time period.
        
        Args:
            start_date: Start date (YYYY-MM-DD) or None for 30 days ago
            end_date: End date (YYYY-MM-DD) or None for today
            datasets: List of datasets to filter (None = all)
        
        Returns:
            CostReport with analysis results
        """
        # Set default dates
        if not end_date:
            end_dt = datetime.now()
            end_date = end_dt.strftime("%Y-%m-%d")
        else:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if not start_date:
            start_dt = end_dt - timedelta(days=30)
            start_date = start_dt.strftime("%Y-%m-%d")
        
        # Query INFORMATION_SCHEMA.JOBS for job statistics
        query = f"""
        SELECT
          job_id,
          user_email,
          TIMESTAMP_MILLIS(creation_time) as creation_time,
          total_bytes_processed,
          total_slot_ms,
          statement_type,
          referenced_tables,
          error_result
        FROM
          `{self.project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE
          DATE(creation_time) BETWEEN '{start_date}' AND '{end_date}'
          AND statement_type IS NOT NULL
          AND total_bytes_processed > 0
        ORDER BY
          total_bytes_processed DESC
        LIMIT 1000
        """
        
        try:
            results = self.client.query(query).result()
        except Exception as e:
            # Fallback: create empty report if query fails
            print(f"Warning: Could not query job history: {e}")
            return CostReport(
                total_cost=0.0,
                query_count=0,
                avg_cost_per_query=0.0,
                bytes_processed=0,
                top_cost_queries=[],
                cost_by_dataset={},
                cost_by_user={}
            )
        
        # Analyze results
        total_bytes = 0
        query_count = 0
        top_queries = []
        cost_by_dataset: Dict[str, float] = {}
        cost_by_user: Dict[str, float] = {}
        
        for row in results:
            bytes_proc = row.total_bytes_processed or 0
            cost = self.calculate_query_cost(bytes_proc)
            
            total_bytes += bytes_proc
            query_count += 1
            
            # Track by user
            user = row.user_email or "unknown"
            cost_by_user[user] = cost_by_user.get(user, 0.0) + cost
            
            # Track by dataset (extract from referenced_tables)
            if row.referenced_tables:
                for table in row.referenced_tables:
                    dataset = table.get("dataset_id", "unknown")
                    if datasets is None or dataset in datasets:
                        cost_by_dataset[dataset] = cost_by_dataset.get(dataset, 0.0) + cost
            
            # Track top expensive queries
            if len(top_queries) < 10:
                top_queries.append({
                    "job_id": row.job_id,
                    "user": user,
                    "bytes_processed": bytes_proc,
                    "cost_usd": round(cost, 4),
                    "creation_time": str(row.creation_time)
                })
        
        # Calculate metrics
        total_cost = self.calculate_query_cost(total_bytes)
        avg_cost = total_cost / query_count if query_count > 0 else 0.0
        
        return CostReport(
            total_cost=round(total_cost, 2),
            query_count=query_count,
            avg_cost_per_query=round(avg_cost, 4),
            bytes_processed=total_bytes,
            top_cost_queries=top_queries,
            cost_by_dataset=cost_by_dataset,
            cost_by_user=cost_by_user
        )
    
    def analyze_table(self, dataset_id: str, table_id: str) -> dict:
        """Analyze a specific table for optimization opportunities.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
        
        Returns:
            Dictionary with table analysis and recommendations
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        table = self.client.get_table(table_ref)
        
        # Collect table metadata
        analysis = {
            "table": table_ref,
            "num_rows": table.num_rows,
            "num_bytes": table.num_bytes,
            "size_gb": round(table.num_bytes / (1024 ** 3), 2),
            "created": str(table.created),
            "modified": str(table.modified),
            "partitioning": None,
            "clustering": None,
            "recommendations": []
        }
        
        # Check partitioning
        if table.time_partitioning:
            analysis["partitioning"] = {
                "type": table.time_partitioning.type_,
                "field": table.time_partitioning.field,
                "expiration_ms": table.time_partitioning.expiration_ms
            }
        else:
            if table.num_bytes > 1024 ** 3:  # > 1 GB
                analysis["recommendations"].append({
                    "type": "partitioning",
                    "priority": "high",
                    "message": "Consider partitioning this table by a date/timestamp column"
                })
        
        # Check clustering
        if table.clustering_fields:
            analysis["clustering"] = table.clustering_fields
        else:
            if table.num_bytes > 1024 ** 3:  # > 1 GB
                analysis["recommendations"].append({
                    "type": "clustering",
                    "priority": "medium",
                    "message": "Consider clustering on frequently filtered columns"
                })
        
        # Check table size
        if table.num_bytes > 100 * (1024 ** 3):  # > 100 GB
            analysis["recommendations"].append({
                "type": "retention",
                "priority": "high",
                "message": "Large table - consider implementing data retention policy"
            })
        
        return analysis
    
    def get_dataset_cost(self, dataset_id: str, days: int = 30) -> dict:
        """Get cost breakdown for a specific dataset.
        
        Args:
            dataset_id: Dataset ID
            days: Number of days to analyze
        
        Returns:
            Dictionary with dataset cost metrics
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        report = self.analyze_period(
            start_date=start_date,
            end_date=end_date,
            datasets=[dataset_id]
        )
        
        dataset_cost = report.cost_by_dataset.get(dataset_id, 0.0)
        
        return {
            "dataset_id": dataset_id,
            "period_days": days,
            "total_cost_usd": round(dataset_cost, 2),
            "daily_avg_cost": round(dataset_cost / days, 2),
            "query_count": report.query_count,
            "total_bytes_processed": report.bytes_processed
        }
    
    @classmethod
    def from_config(cls, config: AnalysisConfig) -> "CostAnalyzer":
        """Create analyzer from configuration.
        
        Args:
            config: AnalysisConfig object
        
        Returns:
            CostAnalyzer instance
        """
        return cls(project_id=config.project_id)

