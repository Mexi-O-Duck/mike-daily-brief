game_plan = []

# SALES ACTION
if "risk-off" in str(what_this_means).lower():
    game_plan.append(
        "Push deals with clear ROI and urgency. Expect more scrutiny from finance."
    )
else:
    game_plan.append(
        "Lean into growth conversations. Good time to position new initiatives."
    )

# INVESTING ACTION
if not ideas_df.empty:
    top = ideas_df.iloc[0]
    if top["1M %"] > 5:
        game_plan.append(
            f"Track {top['Ticker']} closely, but avoid chasing strength after big moves."
        )
    else:
        game_plan.append(
            "No strong momentum trades — better to stay patient today."
        )
else:
    game_plan.append("No strong setups — preserve capital and wait.")

# RISK WATCH
if not data["world_df"].empty:
    game_plan.append(
        "Stay alert to geopolitical headlines — they can shift market sentiment quickly."
    )

# PERSONAL / COST
try:
    if float(data["us_cpi"].get("value", 0)) > 3:
        game_plan.append(
            "Be mindful of cost pressure trends — still impacting spending behavior."
        )
except:
    pass
