"""Judge economics and calibration primitives, without fabricated measurements."""
import math

def calibration_metrics(samples:list[dict],bins:int=10)->dict:
    """Samples: confidence in [0,1], correct boolean; Brier and ECE."""
    if not 1<=bins<=100:raise ValueError("invalid bin count")
    if not samples:raise ValueError("labeled samples required")
    grouped=[[] for _ in range(bins)]
    total=0.0
    for item in samples:
        confidence=float(item["confidence"])
        if not math.isfinite(confidence) or not 0<=confidence<=1:raise ValueError("invalid confidence")
        if not isinstance(item["correct"],bool):raise ValueError("ground truth correctness required")
        y=float(item["correct"])
        total+=(confidence-y)**2
        idx=min(int(confidence*bins),bins-1)
        grouped[idx].append((confidence,y))
    n=len(samples)
    ece=0.0
    nonempty=[]
    for idx,group in enumerate(grouped):
        if not group:continue
        mean_conf=sum(x for x,_ in group)/len(group)
        accuracy=sum(y for _,y in group)/len(group)
        ece+=len(group)/n*abs(mean_conf-accuracy)
        nonempty.append({"bin":idx,"count":len(group),"mean_confidence":mean_conf,"accuracy":accuracy})
    return {"sample_count":n,"brier_score":total/n,"ece":ece,"bins":nonempty,
            "calibrated":False,"note":"descriptive metrics only; independent labels and fit/holdout required"}

def judge_cost(*, input_tokens:int,output_tokens:int,
               input_usd_per_million:float,output_usd_per_million:float)->float:
    vals=(input_tokens,output_tokens,input_usd_per_million,output_usd_per_million)
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in vals):
        raise ValueError("invalid token usage or pricing")
    if not isinstance(input_tokens,int) or not isinstance(output_tokens,int):
        raise ValueError("token counts must be integers")
    return (input_tokens*input_usd_per_million+output_tokens*output_usd_per_million)/1_000_000

def evaluation_economics(samples:list[dict])->dict:
    """Each row: usd, correct, critical, false_accept. Independent ground truth required."""
    if not samples:raise ValueError("evaluation records required")
    total_cost=0.0
    correct_count=false_accept=critical_false_accept=0
    critical_count=0
    for row in samples:
        cost=float(row["usd"])
        if not math.isfinite(cost) or cost<0:raise ValueError("invalid cost")
        if any(not isinstance(row[k],bool) for k in ("correct","critical","false_accept")):
            raise ValueError("labeled boolean outcomes required")
        total_cost+=cost
        correct_count+=row["correct"]
        critical_count+=row["critical"]
        false_accept+=row["false_accept"]
        critical_false_accept+=row["critical"] and row["false_accept"]
    return {"evaluations":len(samples),"judge_cost_usd":total_cost,
            "cost_per_correct_evaluation_usd":total_cost/correct_count if correct_count else None,
            "false_accept_rate":false_accept/len(samples),
            "critical_false_accept_rate":critical_false_accept/critical_count if critical_count else None}
