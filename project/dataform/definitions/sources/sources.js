// Source Table Declarations
// These reference external tables loaded into BigQuery from GCS

// Employees source
declare({
  schema: dataform.projectConfig.vars.raw_dataset,
  name: "raw_employees"
});

// Jobs source
declare({
  schema: dataform.projectConfig.vars.raw_dataset,
  name: "raw_jobs"
});

// Cost Centers source
declare({
  schema: dataform.projectConfig.vars.raw_dataset,
  name: "raw_cost_centers"
});

// Schedules source
declare({
  schema: dataform.projectConfig.vars.raw_dataset,
  name: "raw_schedules"
});

// Timecards source
declare({
  schema: dataform.projectConfig.vars.raw_dataset,
  name: "raw_timecards"
});

// Payroll Runs source
declare({
  schema: dataform.projectConfig.vars.raw_dataset,
  name: "raw_payroll_runs"
});

