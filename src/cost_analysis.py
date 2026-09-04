"""D6 cost-to-serve calculations. Consume measured D4/D5 results; do not rerun the Agent."""

def calculate_run_cost(input_tokens, output_tokens, price_in_per_m, price_out_per_m, tool_fee=0.0):
    return input_tokens/1_000_000*price_in_per_m + output_tokens/1_000_000*price_out_per_m + tool_fee


def build_cost_summary(success_rate, variable_cost_per_run, monthly_fixed_cost=0.0, monthly_volume=8000, failure_cost=7.60):
    expected_failure_cost=(1-success_rate)*failure_cost
    cost_per_successful_task=variable_cost_per_run+expected_failure_cost
    monthly_cost=cost_per_successful_task*monthly_volume+monthly_fixed_cost
    return {"layer1_variable_cost":variable_cost_per_run,"layer2_expected_failure_cost":expected_failure_cost,"layer3_monthly_fixed_cost":monthly_fixed_cost,"cost_per_successful_task":cost_per_successful_task,"monthly_cost":monthly_cost}


def sensitivity(success_rate, variable_cost_per_run, monthly_fixed_cost=0.0, monthly_volume=8000, failure_cost=7.60):
    out={}
    for label,s in [("minus_10pp",max(0,success_rate-0.10)),("base",success_rate),("plus_10pp",min(1,success_rate+0.10))]:
        out[label]=build_cost_summary(s,variable_cost_per_run,monthly_fixed_cost,monthly_volume,failure_cost)
        out[label]["success_rate"]=s
    return out


def break_even_success_rate(cheap_variable_cost, expensive_all_in_success_cost, failure_cost=7.60):
    return 1 - (expensive_all_in_success_cost-cheap_variable_cost)/failure_cost
