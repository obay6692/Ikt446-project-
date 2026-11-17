# Sources and use of external material

## GitHub project consulted

- Alvaro Gonzalez (2026), *Bike-Sharing Hourly Demand Forecasting*:
  https://github.com/alvarogrojas/bike-sharing-demand-forecasting
- Original repository is available under MIT, copyright (c) 2026 Alvaro Gonzalez.
- Upstream source code was **not cloned**, bundled or verbatim copied into this
  zip (network connectivity to GitHub from the build environment failed).
- The upstream project was consulted for its published **methodological approach**:
  temporal partitioning, cyclical calendar features, hourly regression, regression
  metrics and reproducible Python project structure.
- Original UCI results (e.g. RMSE 70) are *not Oslo results* and must **not** be
  included as findings in our IKT466 report.
- This starter was independently written for Oslo City Bike trips with an
  additional PyTorch MLP and a training-fraction comparison, neither presented
  as verified experimental findings at the time of packaging.

If you later copy, adapt, or merge actual code from the original repository,
retain its MIT license and the original copyright notice in the redistributed
copy/substantial portions. Verify any upstream changes.

Original full MIT license URL:
https://github.com/alvarogrojas/bike-sharing-demand-forecasting/blob/main/LICENSE

## Dataset source

- Oslo Bysykkel, Historical Trip Data:
  https://oslobysykkel.no/en/open-data/historical
- License: Norwegian Licence for Open Government Data (NLOD) 2.0,
  https://data.norge.no/nlod/no/2.0
- `started_at` timestamps are counted after conversion to `Europe/Oslo` local
  time; uploaded October 2026 data may start on September 30 in UTC because
  midnight local and UTC differ.

## AI-use disclosure draft (adjust after independently reviewing code)

ChatGPT (OpenAI) was used for planning the experiments, suggesting a Python
project structure, writing draft source code and documentation, and testing
basic functions. The students remain responsible for understanding,
executing, reviewing and correcting the code. All final figures and results
must originate from experiments run on the Oslo Bysykkel data, not from the
AI assistant or a third-party repository.
