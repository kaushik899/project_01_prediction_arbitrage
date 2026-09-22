import "./App.css";

const metrics = [
  {
    value: "19",
    label: "Research Phases",
    detail: "End-to-end pipeline",
  },
  {
    value: "100",
    label: "Markets Monitored",
    detail: "Latest monitoring run",
  },
  {
    value: "69",
    label: "Complete Markets",
    detail: "Validated observations",
  },
  {
    value: "0",
    label: "Positive Net Edge",
    detail: "Latest Phase 18 validation",
  },
];

const researchModules = [
  {
    number: "01",
    title: "Market Intelligence",
    description:
      "Market data, historical observations and time-series analysis across prediction markets.",
    tag: "DATA",
  },
  {
    number: "02",
    title: "Microstructure",
    description:
      "Order-book structure, bid/ask relationships, liquidity and execution conditions.",
    tag: "MARKET",
  },
  {
    number: "03",
    title: "Arbitrage Engine",
    description:
      "Cross-outcome pricing analysis with execution-aware opportunity detection.",
    tag: "ARBITRAGE",
  },
  {
    number: "04",
    title: "Backtesting",
    description:
      "Historical strategy evaluation with execution assumptions and transaction costs.",
    tag: "BACKTEST",
  },
  {
    number: "05",
    title: "Statistical Validation",
    description:
      "Statistical analysis designed to distinguish observed market effects from noise.",
    tag: "RESEARCH",
  },
  {
    number: "06",
    title: "Signal Engine",
    description:
      "Research signals generated from the latest market and cross-market analysis.",
    tag: "SIGNALS",
  },
];

function App() {
  return (
    <div className="app">
      <div className="background-grid" />

      <header className="navbar">
        <a className="brand" href="#top">
          <span className="brand-mark">Q</span>

          <span className="brand-text">
            QUANT
            <strong>ARBITRAGE LAB</strong>
          </span>
        </a>

        <nav className="nav-links">
          <a href="#research">Research</a>
          <a href="#markets">Markets</a>
          <a href="#architecture">Architecture</a>
        </nav>

        <a
          className="github-button"
          href="https://github.com/kaushik899/project_01_prediction_arbitrage"
          target="_blank"
          rel="noreferrer"
        >
          GitHub
          <span>↗</span>
        </a>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="status-dot" />
              RESEARCH ENGINE · PHASE 19
            </div>

            <h1>
              Prediction Markets.
              <br />
              <span>Quantified.</span>
            </h1>

            <p className="hero-description">
              An end-to-end quantitative research platform for prediction
              market pricing, arbitrage analysis, market microstructure,
              execution modelling and signal generation.
            </p>

            <div className="hero-actions">
              <a className="primary-button" href="#research">
                Explore Research
                <span>↓</span>
              </a>

              <a className="secondary-button" href="#markets">
                View Market Data
              </a>
            </div>
          </div>

          <div className="hero-visual" aria-hidden="true">
            <div className="orb orb-one" />
            <div className="orb orb-two" />
            <div className="orb orb-three" />

            <div className="visual-ring ring-one" />
            <div className="visual-ring ring-two" />
            <div className="visual-ring ring-three" />

            <div className="visual-core">
              <span>19</span>
              <small>PHASES</small>
            </div>

            <div className="floating-card card-top">
              <span>MARKETS</span>
              <strong>100</strong>
            </div>

            <div className="floating-card card-bottom">
              <span>COMPLETE</span>
              <strong>69</strong>
            </div>
          </div>
        </section>

        <section className="metrics" id="markets">
          {metrics.map((metric) => (
            <article className="metric-card" key={metric.label}>
              <div className="metric-value">{metric.value}</div>

              <div>
                <div className="metric-label">{metric.label}</div>
                <div className="metric-detail">{metric.detail}</div>
              </div>
            </article>
          ))}
        </section>

        <section className="section" id="research">
          <div className="section-heading">
            <div>
              <div className="section-eyebrow">01 / RESEARCH STACK</div>

              <h2>
                From raw markets
                <br />
                <span>to quantified signals.</span>
              </h2>
            </div>

            <p>
              The platform combines market data, execution modelling,
              historical analysis and statistical validation into one
              research workflow.
            </p>
          </div>

          <div className="module-grid">
            {researchModules.map((module) => (
              <article className="module-card" key={module.number}>
                <div className="module-top">
                  <span className="module-number">{module.number}</span>
                  <span className="module-tag">{module.tag}</span>
                </div>

                <h3>{module.title}</h3>

                <p>{module.description}</p>

                <div className="module-arrow">↗</div>
              </article>
            ))}
          </div>
        </section>

        <section className="terminal-section" id="architecture">
          <div className="terminal-heading">
            <div className="section-eyebrow">02 / SYSTEM STATUS</div>

            <h2>Research pipeline</h2>

            <p>
              Current checkpoint: Phase 19. The Python research engine remains
              separated from the interactive web layer.
            </p>
          </div>

          <div className="terminal">
            <div className="terminal-header">
              <div className="terminal-dots">
                <span />
                <span />
                <span />
              </div>

              <span>quant-arbitrage-lab / system</span>

              <span className="terminal-live">LIVE</span>
            </div>

            <div className="terminal-body">
              <div>
                <span className="terminal-command">$</span>
                pipeline.status()
              </div>

              <div className="terminal-success">
                ✓ Phase 19 signal engine completed
              </div>

              <div>
                <span className="terminal-command">$</span>
                cross_market.validate()
              </div>

              <div className="terminal-success">
                ✓ 69 complete observations
              </div>

              <div>
                <span className="terminal-command">$</span>
                arbitrage.net_edge()
              </div>

              <div className="terminal-muted">
                → Positive net edge: 0
              </div>

              <div>
                <span className="terminal-command">$</span>
                system.ready()
              </div>

              <div className="terminal-success">
                ✓ Research platform ready
              </div>
            </div>
          </div>
        </section>

        <section className="cta-section">
          <div>
            <div className="section-eyebrow">03 / NEXT LAYER</div>

            <h2>
              Research is the engine.
              <br />
              <span>Interaction is the interface.</span>
            </h2>

            <p>
              The next layer connects the quantitative research outputs to
              interactive market visualizations, analytics and 3D exploration.
            </p>
          </div>

          <a
            className="primary-button"
            href="https://github.com/kaushik899/project_01_prediction_arbitrage"
            target="_blank"
            rel="noreferrer"
          >
            Open Repository
            <span>↗</span>
          </a>
        </section>
      </main>

      <footer>
        <span>QUANT ARBITRAGE LAB</span>
        <span>Research checkpoint · Phase 19</span>
      </footer>
    </div>
  );
}

export default App;
