"""Query optimization for BigQuery."""

from typing import Optional, List, Dict
from google.cloud import bigquery
from google.cloud.bigquery import Client

from bq_finops.config import OptimizationConfig


class QueryOptimizer:
    """Optimize BigQuery tables and queries.
    
    This class provides methods to:
    - Apply partitioning to tables
    - Apply clustering to tables
    - Set up data retention policies
    - Generate optimization SQL
    - Validate optimizations
    
    Attributes:
        client: BigQuery client
        project_id: GCP project ID
    """
    
    def __init__(self, project_id: str, client: Optional[Client] = None):
        """Initialize query optimizer.
        
        Args:
            project_id: GCP project ID
            client: Optional BigQuery client (creates new if None)
        """
        self.project_id = project_id
        self.client = client or bigquery.Client(project=project_id)
    
    def generate_partition_ddl(
        self,
        dataset_id: str,
        table_id: str,
        partition_column: str,
        partition_type: str = "DAY"
    ) -> str:
        """Generate DDL to create a partitioned table.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            partition_column: Column to partition by
            partition_type: Partition type (DAY, HOUR, MONTH, YEAR)
        
        Returns:
            CREATE TABLE DDL statement
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        
        # Get existing table schema
        try:
            table = self.client.get_table(table_ref)
            schema_fields = [f"{field.name} {field.field_type}" for field in table.schema]
            schema_str = ",\n  ".join(schema_fields)
        except Exception:
            schema_str = "-- Schema not available, please define manually"
        
        ddl = f"""
-- Create partitioned table: {table_ref}
CREATE OR REPLACE TABLE `{table_ref}`
(
  {schema_str}
)
PARTITION BY {partition_type}({partition_column})
OPTIONS(
  description="Partitioned by {partition_column}",
  partition_expiration_days=NULL
);
""".strip()
        
        return ddl
    
    def generate_cluster_ddl(
        self,
        dataset_id: str,
        table_id: str,
        cluster_columns: List[str],
        partition_column: Optional[str] = None
    ) -> str:
        """Generate DDL to create a clustered table.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            cluster_columns: Columns to cluster by
            partition_column: Optional partition column
        
        Returns:
            CREATE TABLE DDL statement
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        
        # Get existing table schema
        try:
            table = self.client.get_table(table_ref)
            schema_fields = [f"{field.name} {field.field_type}" for field in table.schema]
            schema_str = ",\n  ".join(schema_fields)
        except Exception:
            schema_str = "-- Schema not available, please define manually"
        
        cluster_str = ", ".join(cluster_columns)
        
        ddl_parts = [f"CREATE OR REPLACE TABLE `{table_ref}`", f"(\n  {schema_str}\n)"]
        
        if partition_column:
            ddl_parts.append(f"PARTITION BY DATE({partition_column})")
        
        ddl_parts.append(f"CLUSTER BY {cluster_str}")
        ddl_parts.append(f"OPTIONS(\n  description=\"Clustered by {cluster_str}\"\n);")
        
        ddl = "\n".join(ddl_parts)
        
        return ddl
    
    def set_table_expiration(
        self,
        dataset_id: str,
        table_id: str,
        expiration_days: int
    ) -> bool:
        """Set table expiration/retention policy.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            expiration_days: Days until data expires
        
        Returns:
            True if successful
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        
        try:
            table = self.client.get_table(table_ref)
            
            # Set partition expiration
            if table.time_partitioning:
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=table.time_partitioning.type_,
                    field=table.time_partitioning.field,
                    expiration_ms=expiration_days * 24 * 60 * 60 * 1000
                )
                self.client.update_table(table, ["time_partitioning"])
                print(f"✅ Set partition expiration to {expiration_days} days for {table_ref}")
                return True
            else:
                print(f"⚠️  Table {table_ref} is not partitioned")
                return False
        
        except Exception as e:
            print(f"❌ Error setting expiration: {e}")
            return False
    
    def analyze_query(self, query: str) -> Dict:
        """Analyze a query for optimization opportunities.
        
        Args:
            query: SQL query string
        
        Returns:
            Dictionary with analysis and recommendations
        """
        recommendations = []
        
        query_lower = query.lower()
        
        # Check for SELECT *
        if "select *" in query_lower:
            recommendations.append({
                "type": "select_columns",
                "priority": "high",
                "message": "Avoid SELECT *, specify only needed columns"
            })
        
        # Check for missing WHERE clause
        if "where" not in query_lower and "join" not in query_lower:
            recommendations.append({
                "type": "filtering",
                "priority": "high",
                "message": "Add WHERE clause to filter data and reduce processing"
            })
        
        # Check for LIMIT
        if "limit" not in query_lower:
            recommendations.append({
                "type": "limit",
                "priority": "medium",
                "message": "Consider adding LIMIT clause for exploratory queries"
            })
        
        # Check for partition filter
        if "_table_suffix" in query_lower or "_partitiontime" in query_lower:
            # Good - using partition pruning
            pass
        elif "date(" in query_lower or "timestamp(" in query_lower:
            # Potentially good - date filtering
            pass
        else:
            recommendations.append({
                "type": "partitioning",
                "priority": "medium",
                "message": "Use partition filters to reduce data scanned"
            })
        
        return {
            "query_length": len(query),
            "recommendations": recommendations
        }
    
    def generate_optimization_report(
        self,
        dataset_id: str,
        table_id: str
    ) -> Dict:
        """Generate comprehensive optimization report for a table.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
        
        Returns:
            Dictionary with optimization recommendations
        """
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        
        try:
            table = self.client.get_table(table_ref)
        except Exception as e:
            return {
                "error": f"Could not access table: {e}"
            }
        
        report = {
            "table": table_ref,
            "current_state": {},
            "recommendations": []
        }
        
        # Current partitioning state
        if table.time_partitioning:
            report["current_state"]["partitioned"] = True
            report["current_state"]["partition_field"] = table.time_partitioning.field
            report["current_state"]["partition_type"] = table.time_partitioning.type_
        else:
            report["current_state"]["partitioned"] = False
            if table.num_bytes > 1024 ** 3:  # > 1 GB
                report["recommendations"].append({
                    "action": "add_partitioning",
                    "priority": "high",
                    "benefit": "Reduce query costs by 50-90%",
                    "sql": self.generate_partition_ddl(dataset_id, table_id, "created_at")
                })
        
        # Current clustering state
        if table.clustering_fields:
            report["current_state"]["clustered"] = True
            report["current_state"]["cluster_fields"] = table.clustering_fields
        else:
            report["current_state"]["clustered"] = False
            if table.num_bytes > 1024 ** 3:  # > 1 GB
                report["recommendations"].append({
                    "action": "add_clustering",
                    "priority": "medium",
                    "benefit": "Improve query performance by 10-30%",
                    "sql": "-- Define cluster columns based on query patterns"
                })
        
        # Table size
        size_gb = table.num_bytes / (1024 ** 3)
        report["current_state"]["size_gb"] = round(size_gb, 2)
        
        if size_gb > 100:
            report["recommendations"].append({
                "action": "set_retention",
                "priority": "high",
                "benefit": f"Reduce storage costs (current: {round(size_gb, 2)} GB)",
                "sql": "-- Use ALTER TABLE to set partition expiration"
            })
        
        return report
    
    @classmethod
    def from_config(cls, config: OptimizationConfig) -> "QueryOptimizer":
        """Create optimizer from configuration.
        
        Args:
            config: OptimizationConfig object
        
        Returns:
            QueryOptimizer instance
        """
        return cls(project_id=config.project_id)

