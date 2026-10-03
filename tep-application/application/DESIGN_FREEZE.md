# Extended Tennessee Eastman Process Application — Design Freeze

## Purpose

This application provides external benchmark validation of the monitoring
architecture developed in the main thesis experiment.

The original hybrid methodology is not redesigned or re-optimised for the
Tennessee Eastman Process (TEP). The application adapts an independent
industrial-process benchmark to the existing pipeline and evaluates whether
the frozen monitoring scheme behaves coherently under a known process fault.

The application is intentionally limited in scope so that it remains a short
validation study rather than a second methodological experiment.

## Dataset

The Extended Tennessee Eastman Process reference dataset of Reinartz,
Kulahci and Ravn (2021) will be used.

The TEP dataset is simulated rather than measured plant data, but it represents
a detailed nonlinear, multivariate, closed-loop chemical process and was
published specifically as a benchmark for statistical process monitoring and
fault-detection research.

Only Operating Mode 1 will be considered.

The application will use:

- healthy Mode 1 simulations for Phase-I fitting and calibration;
- independent healthy Mode 1 simulations for in-control validation;
- one pre-specified Mode 1 process fault for out-of-control evaluation;
- the available 25%, 50%, 75% and 100% fault magnitudes.

No fault will be selected after examining which produces the most favourable
result for the hybrid chart.

## Fault

The primary fault is fixed as IDV(2), corresponding to a process-input
composition disturbance.

The same fault family will be evaluated at four available magnitudes:

- 25%
- 50%
- 75%
- 100%

These fault magnitudes are treated as benchmark severity levels and are not
converted into the synthetic experiment's delta scale.

## Relation to the synthetic D1-D5 design

The application preserves the conceptual separation used in the main thesis:

- D1 analogue:
  independent healthy TEP runs used for standardisation and CAE training;

- D2 analogue:
  separate healthy TEP runs used for fitting the OC-SVM to frozen CAE
  representations;

- D3 analogue:
  separate healthy TEP runs used to estimate the in-control monitoring-vector
  moments and empirically calibrate the MEWMA control limit;

- D4 analogue:
  independent healthy TEP runs used only for in-control validation;

- D5 analogue:
  independent IDV(2) fault runs at 25%, 50%, 75% and 100% magnitude.

Simulation runs, rather than overlapping windows from the same run, are the
unit of allocation between fitting, calibration and validation sets.

No run may appear in more than one data role.

## Frozen monitoring architecture

The application retains the thesis architecture:

    multivariate observations
        -> standardisation
        -> overlapping windows
        -> convolutional autoencoder
             -> latent representation
             -> reconstruction error
        -> OC-SVM anomaly score
        -> monitoring vector (OC-SVM score, log SPE)
        -> MEWMA chart

The following design parameters remain fixed unless a purely dimensional
change is required by the TEP input data:

- window length L = 32;
- CAE bottleneck dimension q = 8;
- OC-SVM nu = 0.03;
- OC-SVM gamma = existing median-distance rule;
- MEWMA lambda = 0.05;
- target in-control ARL = 370;
- monitoring vector = [OC-SVM anomaly score, log(SPE)];
- empirical control-limit calibration;
- Phase-I fit/calibration followed by frozen Phase-II evaluation.

The classical raw-data MEWMA remains the primary benchmark.

## Permitted implementation changes

Changes to the original pipeline are limited to those needed to ingest and
process TEP data.

Permitted changes include:

- a TEP dataset loader;
- selection of the documented process-variable set;
- changing the CAE input/output channel count to match the selected TEP
  variables;
- constructing independent TEP fitting/calibration/validation splits;
- handling the known healthy and fault portions of each simulation;
- application-specific result tables and figures.

These are treated as dataset-adaptation changes rather than methodological
redesign.

## Prohibited changes

The following are outside the scope of the application:

- architecture search;
- hyperparameter optimisation;
- changing L, q, nu or lambda after viewing TEP results;
- selecting faults because they make the hybrid appear favourable;
- tuning the control limit using fault data;
- training the CAE or OC-SVM on fault observations;
- conducting another ablation study;
- conducting another smoothing-parameter sensitivity study;
- redesigning the monitoring vector;
- modifying the original synthetic experiment or its results.

## Variable set

The exact Mode 1 process-variable columns will be confirmed directly from the
official Extended TEP files and accompanying documentation before production
execution.

The intention is to use the standard continuously varying process measurements
and manipulated variables suitable for multivariate monitoring, while excluding
columns that are identifiers, timestamps, labels or structurally constant.

Variable inclusion will be determined from dataset documentation and
pre-specified rules, not from fault-response strength.

The final selected variable list must be recorded before the fault results are
examined.

## Fault timing and run-length evaluation

The Extended TEP simulations provide a period of nominal operation followed by
fault activation.

The chart will therefore be allowed to operate during the nominal portion of
each trajectory before the fault occurs.

Detection delay is defined relative to the known fault-onset time.

This differs deliberately from the synthetic thesis experiment, in which the
shift is present from the beginning of the monitored trajectory.

The TEP application therefore provides an additional check of chart behaviour
when the monitoring statistic has reached an in-control operating state before
the disturbance occurs.

## Primary outputs

The application will produce only the outputs needed for the approximately
two-page thesis section:

1. independent in-control performance of:
   - H(0.05), hybrid chart;
   - M(0.05), classical raw-data MEWMA;

2. detection/run-length performance for IDV(2) at:
   - 25%;
   - 50%;
   - 75%;
   - 100% fault magnitude;

3. one compact numerical results table;

4. one primary figure showing detection performance against fault magnitude;

5. a short interpretation comparing the TEP benchmark behaviour with the
   conclusions of the synthetic experiment.

Additional diagnostics may be generated only when needed to verify correctness
of the implementation and will not expand the scientific scope.

## Interpretation rule

The purpose of the application is external benchmark validation, not to prove
that the hybrid chart outperforms the classical MEWMA.

Results will be reported regardless of which chart performs better.

A successful application requires that the frozen monitoring procedure can be
applied coherently to the independent benchmark and that its response to the
known process fault can be interpreted in terms of in-control behaviour and
detection delay.

Because TEP remains a simulated benchmark, the application will not be
described as validation on real plant data.
