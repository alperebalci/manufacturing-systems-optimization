from manufacturing_process_optimization.case06_cnc_parameters import baseline_cnc, optimize_cnc

opt = optimize_cnc()
base = baseline_cnc()
print("optimized cost:", round(opt.objective, 4))
print("baseline cost:", round(base.objective, 4))
print(
    "speed/feed/depth:",
    round(opt.cutting_speed_m_min, 2),
    round(opt.feed_mm_rev, 4),
    round(opt.depth_mm, 3),
)
