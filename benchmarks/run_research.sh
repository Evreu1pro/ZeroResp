#!/bin/bash
cd "E:/g/е/zerope/ZeroResp-main"
RF="python benchmarks/run_field.py"
R="benchmarks/results/research"
mkdir -p $R/v53_sweep $R/v52_sweep $R/full_v53_5 $R/full_v52_5 $R/long_v53 $R/long_v52 $R/tops_v53 $R/tops_v52
TOPS="Evolved FSM 6,EvolvedLookerUp2_2_2,Evolved FSM 16,Evolved HMM 5,PSO Gambler 1_1_1,Evolved ANN 5,Evolved FSM 16 Noise 05,Omega TFT,ZDExtort4,CollectiveStrategy"
( $RF --pack field --turns 200 --reps 8 --seed 42 --noise 0 0.01 0.03 0.05 0.1 --out $R/v53_sweep > $R/log_v53_sweep.txt 2>&1 ) &
( $RF --pack field --turns 200 --reps 8 --seed 42 --noise 0 0.01 0.03 0.05 0.1 --no-ladder --out $R/v52_sweep > $R/log_v52_sweep.txt 2>&1 ) &
( $RF --pack full --turns 200 --reps 1 --seed 42 --noise 0.05 --out $R/full_v53_5 > $R/log_full_v53.txt 2>&1; $RF --pack full --turns 200 --reps 1 --seed 42 --noise 0.05 --no-ladder --out $R/full_v52_5 > $R/log_full_v52.txt 2>&1 ) &
( $RF --pack field --turns 1000 --reps 2 --seed 42 --noise 0 0.05 --out $R/long_v53 > $R/log_long_v53.txt 2>&1; $RF --pack field --turns 1000 --reps 2 --seed 42 --noise 0 0.05 --no-ladder --out $R/long_v52 > $R/log_long_v52.txt 2>&1 ) &
( $RF --vs "$TOPS" --turns 200 --reps 5 --seed 42 --noise 0 0.05 --out $R/tops_v53 > $R/log_tops_v53.txt 2>&1; $RF --vs "$TOPS" --turns 200 --reps 5 --seed 42 --noise 0 0.05 --no-ladder --out $R/tops_v52 > $R/log_tops_v52.txt 2>&1 ) &
wait
echo RESEARCH_ALL_DONE
