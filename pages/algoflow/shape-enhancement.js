(function () {
  const STYLE_ID = "algoflow-shapemap-enhancement-style";
  const PANEL_ATTR = "data-shapemap-enhancement";

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) {
      return;
    }

    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .shape-usage-panel {
        margin: 1rem 0;
        padding: 1rem;
        border: 1px solid rgba(45, 212, 191, 0.18);
        border-radius: 16px;
        background:
          linear-gradient(135deg, rgba(45, 212, 191, 0.08), rgba(167, 139, 250, 0.08)),
          rgba(255, 255, 255, 0.035);
      }

      .shape-usage-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.9rem;
      }

      .shape-usage-kicker {
        color: #2dd4bf;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
      }

      .shape-usage-title {
        margin-top: 0.15rem;
        color: #fff;
        font-size: clamp(1.05rem, 2vw, 1.35rem);
        font-weight: 850;
        letter-spacing: -0.02em;
      }

      .shape-usage-copy {
        max-width: 760px;
        color: #9ca3af;
        font-size: 0.84rem;
        line-height: 1.65;
      }

      .shape-product-strip {
        display: grid;
        grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
        gap: 0.75rem;
        margin: 1rem 0;
      }

      .shape-product-card,
      .shape-recent-card {
        border: 1px solid rgba(45, 212, 191, 0.17);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(45, 212, 191, 0.08), rgba(15, 23, 42, 0.24)),
          rgba(3, 7, 18, 0.48);
        overflow: hidden;
      }

      .shape-product-card {
        padding: 0.95rem;
      }

      .shape-product-card b,
      .shape-recent-head b {
        display: block;
        color: #5eead4;
        font-size: 0.68rem;
        font-weight: 850;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .shape-product-card strong {
        display: block;
        margin-top: 0.35rem;
        color: #f8fafc;
        font-size: 1.05rem;
        line-height: 1.25;
      }

      .shape-product-card p {
        margin: 0.45rem 0 0;
        color: #94a3b8;
        font-size: 0.76rem;
        line-height: 1.55;
      }

      .shape-user-path {
        display: grid;
        gap: 0.55rem;
        margin-top: 0.75rem;
      }

      .shape-user-path-step {
        display: grid;
        grid-template-columns: 30px minmax(0, 1fr);
        gap: 0.55rem;
        align-items: start;
        padding: 0.58rem;
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 11px;
        background: rgba(2, 6, 23, 0.34);
      }

      .shape-user-path-step em {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.55rem;
        height: 1.55rem;
        border-radius: 50%;
        color: #042f2e;
        background: #5eead4;
        font-style: normal;
        font-size: 0.72rem;
        font-weight: 900;
      }

      .shape-user-path-step span {
        display: block;
        color: #e5e7eb;
        font-size: 0.77rem;
        font-weight: 800;
      }

      .shape-user-path-step small {
        display: block;
        margin-top: 0.2rem;
        color: #94a3b8;
        font-size: 0.7rem;
        line-height: 1.42;
      }

      .shape-recent-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.85rem 0.9rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }

      .shape-recent-head span {
        display: block;
        margin-top: 0.24rem;
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.42;
      }

      .shape-recent-state {
        flex-shrink: 0;
        padding: 0.34rem 0.5rem;
        border: 1px solid rgba(251, 191, 36, 0.28);
        border-radius: 999px;
        color: #fde68a;
        background: rgba(251, 191, 36, 0.1);
        font-size: 0.64rem;
        font-weight: 850;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .shape-recent-list {
        display: grid;
      }

      .shape-recent-row {
        display: grid;
        grid-template-columns: 68px minmax(0, 1fr) 82px;
        gap: 0.6rem;
        align-items: center;
        padding: 0.72rem 0.9rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
      }

      .shape-recent-row:last-child {
        border-bottom: 0;
      }

      .shape-recent-type {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 28px;
        border-radius: 999px;
        color: #bfdbfe;
        background: rgba(96, 165, 250, 0.12);
        font-size: 0.7rem;
        font-weight: 850;
      }

      .shape-recent-type.buy {
        color: #bbf7d0;
        background: rgba(34, 197, 94, 0.13);
      }

      .shape-recent-type.sell {
        color: #fecaca;
        background: rgba(248, 113, 113, 0.13);
      }

      .shape-recent-route {
        min-width: 0;
        display: flex;
        align-items: center;
        gap: 0.38rem;
        color: #f8fafc;
        font-size: 0.8rem;
        font-weight: 850;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .shape-recent-route small {
        color: #64748b;
        font-size: 0.68rem;
        font-weight: 800;
      }

      .shape-recent-time {
        color: #64748b;
        font-size: 0.68rem;
        text-align: right;
      }

      .shape-next-actions {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.6rem;
        margin: 0.85rem 0 1rem;
      }

      .shape-next-action {
        padding: 0.72rem;
        border: 1px solid rgba(45, 212, 191, 0.14);
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.38);
      }

      .shape-next-action b {
        display: block;
        color: #ccfbf1;
        font-size: 0.78rem;
      }

      .shape-next-action span {
        display: block;
        margin-top: 0.28rem;
        color: #94a3b8;
        font-size: 0.7rem;
        line-height: 1.42;
      }

      .shape-dashboard-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 1rem 0;
      }

      .shape-dashboard-card {
        min-height: 104px;
        padding: 0.85rem;
        border: 1px solid rgba(45, 212, 191, 0.16);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(45, 212, 191, 0.08), rgba(15, 23, 42, 0.18)),
          rgba(3, 7, 18, 0.46);
      }

      .shape-dashboard-card b {
        display: block;
        color: #94a3b8;
        font-size: 0.66rem;
        font-weight: 850;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .shape-dashboard-card strong {
        display: block;
        margin-top: 0.32rem;
        color: #f8fafc;
        font-size: 0.98rem;
        line-height: 1.25;
      }

      .shape-dashboard-card span {
        display: block;
        margin-top: 0.42rem;
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.45;
      }

      .shape-signal-deck {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.7rem;
        margin: 1rem 0;
      }

      .shape-signal-card {
        min-height: 180px;
        padding: 0.9rem;
        border: 1px solid rgba(94, 234, 212, 0.16);
        border-radius: 14px;
        background:
          linear-gradient(145deg, rgba(94, 234, 212, 0.08), rgba(15, 23, 42, 0.2)),
          rgba(3, 7, 18, 0.44);
      }

      .shape-signal-card b {
        display: block;
        color: #5eead4;
        font-size: 0.68rem;
        font-weight: 850;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .shape-signal-card strong {
        display: block;
        margin-top: 0.34rem;
        color: #f8fafc;
        font-size: 1rem;
        line-height: 1.25;
      }

      .shape-signal-card span,
      .shape-signal-card li {
        color: #94a3b8;
        font-size: 0.74rem;
        line-height: 1.5;
      }

      .shape-signal-card ul {
        margin: 0.55rem 0 0;
        padding-left: 1rem;
      }

      .shape-signal-status {
        display: inline-flex;
        align-items: center;
        margin-top: 0.65rem;
        padding: 0.35rem 0.55rem;
        border-radius: 999px;
        border: 1px solid rgba(45, 212, 191, 0.18);
        color: #ccfbf1;
        background: rgba(13, 148, 136, 0.12);
        font-size: 0.68rem;
        font-weight: 800;
      }

      .shape-daily-scanner {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
        gap: 0.75rem;
        margin: 1rem 0;
      }

      .shape-start-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.7rem;
        margin: 1rem 0;
      }

      .shape-start-step {
        position: relative;
        min-height: 116px;
        padding: 0.85rem 0.85rem 0.85rem 3rem;
        border: 1px solid rgba(45, 212, 191, 0.16);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(13, 148, 136, 0.11), rgba(15, 23, 42, 0.18)),
          rgba(3, 7, 18, 0.42);
      }

      .shape-start-step em {
        position: absolute;
        left: 0.82rem;
        top: 0.82rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.45rem;
        height: 1.45rem;
        border-radius: 50%;
        color: #022c22;
        background: #5eead4;
        font-style: normal;
        font-size: 0.72rem;
        font-weight: 900;
      }

      .shape-start-step b {
        display: block;
        color: #f8fafc;
        font-size: 0.85rem;
      }

      .shape-start-step span {
        display: block;
        margin-top: 0.34rem;
        color: #94a3b8;
        font-size: 0.74rem;
        line-height: 1.5;
      }

      .shape-daily-panel {
        border: 1px solid rgba(45, 212, 191, 0.16);
        border-radius: 14px;
        padding: 0.9rem;
        background:
          linear-gradient(135deg, rgba(45, 212, 191, 0.07), rgba(15, 23, 42, 0.2)),
          rgba(3, 7, 18, 0.44);
      }

      .shape-daily-panel b {
        display: block;
        color: #5eead4;
        font-size: 0.7rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .shape-daily-panel strong {
        display: block;
        margin-top: 0.35rem;
        color: #f8fafc;
        font-size: 1rem;
        line-height: 1.25;
      }

      .shape-daily-panel span,
      .shape-daily-panel li {
        color: #94a3b8;
        font-size: 0.74rem;
        line-height: 1.5;
      }

      .shape-daily-panel ul {
        margin: 0.55rem 0 0;
        padding-left: 1rem;
      }

      .shape-scanner-feed {
        display: grid;
        gap: 0.5rem;
        margin-top: 0.65rem;
      }

      .shape-scanner-feed-row {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        gap: 0.55rem;
        align-items: center;
        padding: 0.55rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 11px;
        background: rgba(2, 6, 23, 0.36);
      }

      .shape-scanner-feed-type {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 54px;
        min-height: 28px;
        border-radius: 999px;
        border: 1px solid rgba(45, 212, 191, 0.22);
        color: #ccfbf1;
        background: rgba(13, 148, 136, 0.13);
        font-size: 0.68rem;
        font-weight: 850;
      }

      .shape-scanner-feed-route {
        min-width: 0;
        color: #f8fafc;
        font-size: 0.78rem;
        font-weight: 800;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .shape-scanner-feed-state {
        color: #64748b;
        font-size: 0.68rem;
        white-space: nowrap;
      }

      .shape-scanner-board {
        margin: 1rem 0;
        border: 1px solid rgba(45, 212, 191, 0.16);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(15, 23, 42, 0.54), rgba(8, 47, 73, 0.22)),
          rgba(3, 7, 18, 0.46);
        overflow: hidden;
      }

      .shape-scanner-board-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.9rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }

      .shape-scanner-board-head b {
        display: block;
        color: #f8fafc;
        font-size: 0.92rem;
      }

      .shape-scanner-board-head span {
        display: block;
        margin-top: 0.28rem;
        color: #94a3b8;
        font-size: 0.73rem;
        line-height: 1.45;
      }

      .shape-scanner-board-state {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: max-content;
        padding: 0.35rem 0.55rem;
        border-radius: 999px;
        border: 1px solid rgba(251, 191, 36, 0.28);
        background: rgba(251, 191, 36, 0.1);
        color: #fde68a;
        font-size: 0.66rem;
        font-weight: 850;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .shape-scanner-board-body {
        display: grid;
        gap: 0;
      }

      .shape-scanner-board-row {
        display: grid;
        grid-template-columns: 88px minmax(0, 1.25fr) minmax(0, 1fr) 92px;
        gap: 0.65rem;
        align-items: center;
        padding: 0.72rem 0.9rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
      }

      .shape-scanner-board-row:last-child {
        border-bottom: 0;
      }

      .shape-board-kind {
        display: inline-flex;
        justify-content: center;
        padding: 0.34rem 0.48rem;
        border-radius: 999px;
        background: rgba(96, 165, 250, 0.11);
        color: #bfdbfe;
        font-size: 0.68rem;
        font-weight: 850;
      }

      .shape-board-route {
        min-width: 0;
        color: #f8fafc;
        font-size: 0.82rem;
        font-weight: 850;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .shape-board-note {
        min-width: 0;
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.35;
      }

      .shape-board-evidence {
        color: #5eead4;
        font-size: 0.68rem;
        font-weight: 850;
        text-align: right;
      }

      .shape-journey-panel {
        margin: 1rem 0;
        padding: 0.9rem;
        border: 1px solid rgba(96, 165, 250, 0.16);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(96, 165, 250, 0.07), rgba(45, 212, 191, 0.05)),
          rgba(3, 7, 18, 0.42);
      }

      .shape-journey-title {
        color: #f8fafc;
        font-size: 0.92rem;
        font-weight: 850;
      }

      .shape-journey-copy {
        margin-top: 0.25rem;
        color: #94a3b8;
        font-size: 0.75rem;
        line-height: 1.5;
      }

      .shape-journey-steps {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin-top: 0.75rem;
      }

      .shape-journey-step {
        min-height: 86px;
        padding: 0.75rem;
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.38);
      }

      .shape-journey-step b {
        display: block;
        color: #5eead4;
        font-size: 0.74rem;
      }

      .shape-journey-step span {
        display: block;
        margin-top: 0.32rem;
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.42;
      }

      .shape-action-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
      }

      .shape-action-card {
        min-height: 112px;
        padding: 0.9rem;
        border: 1px solid rgba(45, 212, 191, 0.16);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(45, 212, 191, 0.08), rgba(15, 23, 42, 0.18)),
          rgba(3, 7, 18, 0.44);
      }

      .shape-action-card b {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        color: #ccfbf1;
        font-size: 0.82rem;
      }

      .shape-action-card span {
        display: block;
        margin-top: 0.45rem;
        color: #94a3b8;
        font-size: 0.75rem;
        line-height: 1.55;
      }

      .shape-goal-panel {
        margin: 1rem 0;
        border: 1px solid rgba(167, 139, 250, 0.18);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(167, 139, 250, 0.08), rgba(45, 212, 191, 0.05)),
          rgba(3, 7, 18, 0.42);
        overflow: hidden;
      }

      .shape-goal-head,
      .shape-goal-body {
        padding: 0.9rem;
      }

      .shape-goal-head {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }

      .shape-goal-head b {
        display: block;
        color: #f8fafc;
        font-size: 0.92rem;
      }

      .shape-goal-head span {
        display: block;
        margin-top: 0.22rem;
        color: #94a3b8;
        font-size: 0.75rem;
        line-height: 1.5;
      }

      .shape-goal-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
      }

      .shape-goal-button {
        min-height: 96px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 12px;
        padding: 0.8rem;
        text-align: left;
        color: #e5e7eb;
        background: rgba(15, 23, 42, 0.42);
        cursor: pointer;
        font: inherit;
      }

      .shape-goal-button:hover,
      .shape-goal-button[aria-pressed="true"] {
        border-color: rgba(45, 212, 191, 0.42);
        background: rgba(13, 148, 136, 0.14);
      }

      .shape-goal-button b {
        display: block;
        color: #ccfbf1;
        font-size: 0.82rem;
      }

      .shape-goal-button span {
        display: block;
        margin-top: 0.35rem;
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.45;
      }

      .shape-goal-output {
        margin-top: 0.75rem;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.65rem;
      }

      .shape-goal-output-card {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.8rem;
        background: rgba(2, 6, 23, 0.4);
      }

      .shape-goal-output-card b {
        display: block;
        color: #a78bfa;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .shape-goal-output-card strong {
        display: block;
        margin-top: 0.3rem;
        color: #f8fafc;
        font-size: 0.92rem;
      }

      .shape-goal-output-card span,
      .shape-goal-output-card li {
        color: #94a3b8;
        font-size: 0.74rem;
        line-height: 1.5;
      }

      .shape-goal-output-card ul {
        margin: 0.5rem 0 0;
        padding-left: 1rem;
      }

      .shape-scan-console {
        margin: 1rem 0;
        border: 1px solid rgba(45, 212, 191, 0.18);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(45, 212, 191, 0.07), rgba(15, 23, 42, 0.24)),
          rgba(3, 7, 18, 0.48);
        overflow: hidden;
      }

      .shape-scan-console-head,
      .shape-scan-console-body,
      .shape-scan-console-result {
        padding: 0.9rem;
      }

      .shape-scan-console-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.85rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }

      .shape-scan-console-head b {
        color: #f8fafc;
        font-size: 0.92rem;
      }

      .shape-scan-console-head span {
        color: #94a3b8;
        font-size: 0.74rem;
        line-height: 1.45;
      }

      .shape-scan-mode {
        flex-shrink: 0;
        border: 1px solid rgba(45, 212, 191, 0.25);
        border-radius: 999px;
        padding: 0.32rem 0.65rem;
        color: #5eead4;
        background: rgba(13, 148, 136, 0.1);
        font-size: 0.66rem;
        font-weight: 850;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .shape-scan-input-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 0.6rem;
      }

      .shape-scan-input {
        width: 100%;
        min-height: 42px;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 12px;
        padding: 0.65rem 0.8rem;
        color: #f8fafc;
        background: rgba(2, 6, 23, 0.62);
        font: inherit;
        font-size: 0.82rem;
        outline: none;
      }

      .shape-scan-input:focus {
        border-color: rgba(45, 212, 191, 0.55);
        box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.09);
      }

      .shape-scan-run,
      .shape-preset-button {
        min-height: 42px;
        border: 1px solid rgba(45, 212, 191, 0.25);
        border-radius: 12px;
        padding: 0.58rem 0.78rem;
        color: #ccfbf1;
        background: rgba(13, 148, 136, 0.13);
        cursor: pointer;
        font: inherit;
        font-size: 0.72rem;
        font-weight: 850;
      }

      .shape-scan-run:hover,
      .shape-preset-button:hover {
        border-color: rgba(45, 212, 191, 0.44);
        background: rgba(13, 148, 136, 0.22);
      }

      .shape-preset-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.65rem;
      }

      .shape-preset-label {
        color: #64748b;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .shape-scan-console-result {
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(15, 23, 42, 0.34);
      }

      .shape-result-grid {
        display: grid;
        grid-template-columns: 1.1fr 0.9fr;
        gap: 0.75rem;
      }

      .shape-result-card {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.85rem;
        background: rgba(2, 6, 23, 0.36);
      }

      .shape-result-card b {
        display: block;
        color: #2dd4bf;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .shape-result-card strong {
        display: block;
        margin-top: 0.32rem;
        color: #f8fafc;
        font-size: 1rem;
      }

      .shape-result-card span,
      .shape-result-card li {
        color: #94a3b8;
        font-size: 0.75rem;
        line-height: 1.5;
      }

      .shape-result-card ul {
        margin: 0.55rem 0 0;
        padding-left: 1.05rem;
      }

      .shape-usage-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
      }

      .shape-usage-card {
        min-height: 108px;
        padding: 0.85rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        background: rgba(10, 9, 27, 0.42);
      }

      .shape-usage-card strong {
        display: block;
        margin-bottom: 0.25rem;
        color: #e5e7eb;
        font-size: 0.83rem;
      }

      .shape-usage-card span {
        display: block;
        color: #6b7280;
        font-size: 0.76rem;
        line-height: 1.55;
      }

      .shape-usage-flow {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        flex-wrap: wrap;
        color: #6b7280;
        font-size: 0.76rem;
        font-weight: 650;
      }

      .shape-usage-flow b {
        color: #2dd4bf;
        font-weight: 800;
      }

      .shape-usage-safe {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        flex-shrink: 0;
        border: 1px solid rgba(16, 185, 129, 0.28);
        border-radius: 999px;
        padding: 0.35rem 0.7rem;
        color: #34d399;
        background: rgba(16, 185, 129, 0.09);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .shape-usage-actions {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin: 1rem 0 0.85rem;
      }

      .shape-usage-links {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        flex-wrap: wrap;
      }

      .shape-usage-link,
      .shape-usage-copy-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        min-height: 38px;
        border: 1px solid rgba(45, 212, 191, 0.22);
        border-radius: 999px;
        padding: 0.45rem 0.75rem;
        color: #ccfbf1;
        background: rgba(13, 148, 136, 0.11);
        font-size: 0.72rem;
        font-weight: 800;
        text-decoration: none;
      }

      .shape-usage-copy-btn {
        cursor: pointer;
        font-family: inherit;
      }

      .shape-usage-link:hover,
      .shape-usage-copy-btn:hover {
        border-color: rgba(45, 212, 191, 0.42);
        background: rgba(13, 148, 136, 0.18);
      }

      .shape-scan-brief {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.85rem 0;
      }

      .shape-scan-card {
        min-height: 96px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.85rem;
        background: rgba(3, 7, 18, 0.38);
      }

      .shape-scan-card b {
        display: block;
        color: #2dd4bf;
        font-size: 0.7rem;
        letter-spacing: 0.11em;
        text-transform: uppercase;
      }

      .shape-scan-card strong {
        display: block;
        margin-top: 0.35rem;
        color: #f8fafc;
        font-size: 0.95rem;
      }

      .shape-scan-card span {
        display: block;
        margin-top: 0.25rem;
        color: #94a3b8;
        font-size: 0.75rem;
        line-height: 1.5;
      }

      .shape-market-preview {
        margin: 0.85rem 0;
        border: 1px solid rgba(45, 212, 191, 0.16);
        border-radius: 14px;
        background:
          linear-gradient(135deg, rgba(45, 212, 191, 0.08), rgba(15, 23, 42, 0.28)),
          rgba(2, 6, 23, 0.42);
        overflow: hidden;
      }

      .shape-market-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.85rem;
        padding: 0.9rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      }

      .shape-market-head b {
        display: block;
        color: #f8fafc;
        font-size: 0.94rem;
      }

      .shape-market-head span {
        display: block;
        margin-top: 0.25rem;
        color: #94a3b8;
        font-size: 0.74rem;
        line-height: 1.5;
      }

      .shape-market-pill {
        flex-shrink: 0;
        border: 1px solid rgba(251, 191, 36, 0.28);
        border-radius: 999px;
        padding: 0.32rem 0.65rem;
        color: #fbbf24;
        background: rgba(251, 191, 36, 0.1);
        font-size: 0.66rem;
        font-weight: 850;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .shape-market-body {
        padding: 0.9rem;
      }

      .shape-market-grid {
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 0.75rem;
      }

      .shape-activity-list,
      .shape-watchlist {
        display: grid;
        gap: 0.6rem;
      }

      .shape-activity-row,
      .shape-watch-card {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        background: rgba(3, 7, 18, 0.38);
      }

      .shape-activity-row {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.7rem;
        padding: 0.72rem;
      }

      .shape-activity-type {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 76px;
        min-height: 32px;
        border-radius: 999px;
        color: #ccfbf1;
        background: rgba(13, 148, 136, 0.14);
        border: 1px solid rgba(45, 212, 191, 0.22);
        font-size: 0.7rem;
        font-weight: 850;
      }

      .shape-activity-main {
        min-width: 0;
      }

      .shape-activity-route {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        flex-wrap: wrap;
        color: #e5e7eb;
        font-size: 0.82rem;
        font-weight: 800;
      }

      .shape-token-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.32rem;
        border-radius: 999px;
        padding: 0.22rem 0.48rem;
        background: rgba(255, 255, 255, 0.07);
        color: #f8fafc;
      }

      .shape-token-chip img {
        width: 18px;
        height: 18px;
        border-radius: 50%;
      }

      .shape-activity-note {
        display: block;
        margin-top: 0.28rem;
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.45;
      }

      .shape-activity-status {
        justify-self: end;
        color: #64748b;
        font-size: 0.7rem;
        white-space: nowrap;
      }

      .shape-watch-card {
        padding: 0.78rem;
      }

      .shape-watch-card b {
        display: block;
        color: #2dd4bf;
        font-size: 0.68rem;
        letter-spacing: 0.11em;
        text-transform: uppercase;
      }

      .shape-watch-card strong {
        display: block;
        margin-top: 0.32rem;
        color: #f8fafc;
        font-size: 0.9rem;
      }

      .shape-watch-card span {
        display: block;
        margin-top: 0.24rem;
        color: #94a3b8;
        font-size: 0.73rem;
        line-height: 1.45;
      }

      .shape-legend {
        margin: 0.85rem 0;
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
      }

      .shape-legend-item {
        min-height: 88px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.75rem;
        background: rgba(3, 7, 18, 0.34);
      }

      .shape-legend-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        margin-bottom: 0.42rem;
        border: 1px solid rgba(45, 212, 191, 0.3);
        color: #2dd4bf;
        background: rgba(13, 148, 136, 0.12);
        font-size: 0.72rem;
        font-weight: 900;
      }

      .shape-legend-mark.asset {
        border-radius: 50%;
      }

      .shape-legend-mark.wallet {
        border-radius: 7px;
      }

      .shape-legend-mark.pool {
        transform: rotate(45deg);
        border-radius: 6px;
      }

      .shape-legend-mark.pool span {
        transform: rotate(-45deg);
      }

      .shape-legend-mark.review {
        border-color: rgba(251, 191, 36, 0.35);
        color: #fbbf24;
        background: rgba(251, 191, 36, 0.1);
        clip-path: polygon(50% 0, 100% 100%, 0 100%);
      }

      .shape-legend-item b {
        display: block;
        color: #e5e7eb;
        font-size: 0.78rem;
      }

      .shape-legend-item span {
        display: block;
        margin-top: 0.22rem;
        color: #94a3b8;
        font-size: 0.72rem;
        line-height: 1.45;
      }

      .shape-report-template {
        margin: 0.85rem 0 1rem;
        padding: 0.85rem;
        border: 1px solid rgba(167, 139, 250, 0.2);
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.48);
      }

      .shape-report-template b {
        display: block;
        color: #c4b5fd;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .shape-report-template pre {
        margin: 0.55rem 0 0;
        white-space: pre-wrap;
        color: #d1d5db;
        font-size: 0.75rem;
        line-height: 1.55;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      }

      @media (max-width: 920px) {
        .shape-dashboard-grid,
        .shape-action-strip,
        .shape-next-actions,
        .shape-start-strip,
        .shape-goal-grid,
        .shape-goal-output,
        .shape-usage-grid,
        .shape-result-grid,
        .shape-market-grid,
        .shape-product-strip,
        .shape-daily-scanner,
        .shape-journey-steps,
        .shape-legend {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .shape-scan-brief {
          grid-template-columns: 1fr;
        }

        .shape-scanner-board-row {
          grid-template-columns: 76px minmax(0, 1fr);
        }

        .shape-board-note,
        .shape-board-evidence {
          grid-column: 2;
          text-align: left;
        }
      }

      @media (max-width: 560px) {
        .shape-usage-top {
          flex-direction: column;
        }

        .shape-dashboard-grid,
        .shape-action-strip,
        .shape-next-actions,
        .shape-start-strip,
        .shape-goal-grid,
        .shape-goal-output,
        .shape-usage-grid,
        .shape-result-grid,
        .shape-market-grid,
        .shape-product-strip,
        .shape-daily-scanner,
        .shape-journey-steps,
        .shape-legend {
          grid-template-columns: 1fr;
        }

        .shape-scan-console-head,
        .shape-scanner-board-head,
        .shape-market-head,
        .shape-scan-input-row {
          grid-template-columns: 1fr;
          flex-direction: column;
          align-items: stretch;
        }

        .shape-activity-row {
          grid-template-columns: 1fr;
          align-items: stretch;
        }

        .shape-scanner-feed-row {
          grid-template-columns: 1fr;
          align-items: stretch;
        }

        .shape-recent-head {
          flex-direction: column;
        }

        .shape-recent-row {
          grid-template-columns: 1fr;
          align-items: stretch;
        }

        .shape-recent-route {
          white-space: normal;
        }

        .shape-recent-time {
          text-align: left;
        }

        .shape-scanner-board-row {
          grid-template-columns: 1fr;
          align-items: stretch;
        }

        .shape-board-note,
        .shape-board-evidence {
          grid-column: auto;
        }

        .shape-activity-status {
          justify-self: start;
        }
      }
    `;
    document.head.appendChild(style);
  }

  const PRESET_VALUES = {
    pnet: "3169177585",
    wallet: "Paste wallet address",
    pool: "Paste pool or app ID",
  };

  const RESULT_COPY = {
    asset: {
      label: "Asset scan",
      title: "PNET asset lens ready",
      summary:
        "Use this as the default PNET transparency scan: verify ASA identity, then review holder concentration and liquidity context.",
      next: [
        "Open the public asset page before making public claims.",
        "Review holder concentration and wallet-role labels.",
        "Use market evidence only as context, not as trading advice.",
      ],
      evidence: [
        "ASA: 3169177585",
        "Mode: read-only",
        "Boundary: no signing or transaction submission",
      ],
    },
    wallet: {
      label: "Wallet scan",
      title: "Wallet role review",
      summary:
        "Classify the wallet as creator, LP, whale, community, or unknown before it appears in a transparency update.",
      next: [
        "Check whether the wallet holds PNET, LP tokens, or related assets.",
        "Look for repeated sends, receives, or pool interactions.",
        "Do not publish private identity claims from address-only evidence.",
      ],
      evidence: [
        "Role labels are research notes, not identity proof.",
        "Use explorer links for public verification.",
        "No wallet connection required.",
      ],
    },
    pool: {
      label: "Pool or app scan",
      title: "Liquidity context review",
      summary:
        "Use pool/app IDs to build a read-only liquidity picture before talking about LP depth or market context.",
      next: [
        "Confirm the pool/app belongs to the expected asset pair.",
        "Compare recent public activity against holder distribution.",
        "Avoid executable route, buy/sell, or LP-deposit instructions.",
      ],
      evidence: [
        "Pool/app context is public evidence only.",
        "No arbitrage execution is exposed.",
        "No deposit or swap action is available here.",
      ],
    },
    unknown: {
      label: "Manual review",
      title: "Target needs manual classification",
      summary:
        "This input does not look like the default PNET ASA, a simple numeric ID, or a full wallet address.",
      next: [
        "Paste ASA 3169177585 for the default PNET scan.",
        "Paste a full Algorand address for wallet role review.",
        "Paste a numeric pool/app/ASA ID for public evidence lookup.",
      ],
      evidence: [
        "No live API request was made.",
        "No signing or wallet connection was requested.",
        "Treat the result as a prompt for manual research.",
      ],
    },
  };

  const GOAL_COPY = {
    pnet: {
      title: "Verify PNET before sharing it",
      outcome: "A public-safe PNET transparency summary.",
      steps: [
        "Start from ASA 3169177585.",
        "Open the asset and explorer links.",
        "Record holder, pool, and liquidity notes without price claims.",
      ],
      report:
        "PNET ShapeMap: asset verified, public links checked, holder/pool notes prepared, no buy/sell or investment claim.",
    },
    wallet: {
      title: "Understand a wallet role",
      outcome: "A cautious role label for public research.",
      steps: [
        "Paste the full Algorand address.",
        "Classify only from public evidence: creator, LP, whale, community, or unknown.",
        "Avoid identity claims unless the wallet owner has verified them elsewhere.",
      ],
      report:
        "Wallet ShapeMap: address reviewed for role context, evidence remains public, identity and intent are not assumed.",
    },
    update: {
      title: "Prepare a community update",
      outcome: "A short transparency note that people can verify.",
      steps: [
        "Use the PNET preset first.",
        "Add only read-only evidence links.",
        "Copy the scan checklist and paste it into GitHub, Discord, or a public update.",
      ],
      report:
        "Community ShapeMap: PNET context summarized with evidence links, no fresh route, no trading instruction, no hype.",
    },
  };

  function classifyInput(value) {
    const normalized = value.trim();

    const lower = normalized.toLowerCase();

    if (!normalized || lower === "pnet" || normalized === "3169177585") {
      return "asset";
    }

    if (lower === "paste wallet address") {
      return "wallet";
    }

    if (lower === "paste pool or app id") {
      return "pool";
    }

    if (/^[A-Z2-7]{58}$/.test(normalized)) {
      return "wallet";
    }

    if (/^\d{4,}$/.test(normalized)) {
      return "pool";
    }

    return "unknown";
  }

  function renderScanResult(panel, value) {
    const resultTarget = panel.querySelector("[data-shape-scan-result]");
    if (!resultTarget) {
      return;
    }

    const type = classifyInput(value);
    const copy = RESULT_COPY[type];
    resultTarget.innerHTML = `
      <div class="shape-result-grid">
        <div class="shape-result-card">
          <b>${copy.label}</b>
          <strong>${copy.title}</strong>
          <span>${copy.summary}</span>
          <ul>
            ${copy.next.map((item) => `<li>${item}</li>`).join("")}
          </ul>
        </div>
        <div class="shape-result-card">
          <b>Evidence boundaries</b>
          <strong>${type === "unknown" ? "Not classified" : "Safe to inspect"}</strong>
          <ul>
            ${copy.evidence.map((item) => `<li>${item}</li>`).join("")}
          </ul>
        </div>
      </div>
    `;
  }

  function renderGoal(panel, goalKey) {
    const goal = GOAL_COPY[goalKey] || GOAL_COPY.pnet;
    const outputTarget = panel.querySelector("[data-shape-goal-output]");
    if (!outputTarget) {
      return;
    }

    panel.querySelectorAll("[data-shape-goal]").forEach((button) => {
      button.setAttribute("aria-pressed", button.dataset.shapeGoal === goalKey ? "true" : "false");
    });

    outputTarget.innerHTML = `
      <div class="shape-goal-output-card">
        <b>What this unlocks</b>
        <strong>${goal.title}</strong>
        <span>${goal.outcome}</span>
        <ul>
          ${goal.steps.map((step) => `<li>${step}</li>`).join("")}
        </ul>
      </div>
      <div class="shape-goal-output-card">
        <b>Copy-ready output</b>
        <strong>Safe report wording</strong>
        <span data-shape-goal-report>${goal.report}</span>
      </div>
    `;
  }

  function createPanel() {
    const panel = document.createElement("section");
    panel.className = "shape-usage-panel";
    panel.setAttribute(PANEL_ATTR, "true");
    panel.innerHTML = `
      <div class="shape-usage-top">
        <div>
          <div class="shape-usage-kicker">AlgoShapes · PNET market map</div>
          <div class="shape-usage-title">PNET Shape Scanner: read the market in one minute.</div>
        </div>
        <div class="shape-usage-safe">Guest friendly · no signing</div>
      </div>
      <p class="shape-usage-copy">
        Track PNET holders, pools, swaps, and liquidity health from one read-only scanner entry point. A guest should immediately see what to inspect:
        PNET identity, recent activity context, holder concentration, pool health, and shareable transparency evidence.
        Live swap feeds and LP-pool depth remain future-gated until API QA and redaction review pass.
      </p>
      <div class="shape-product-strip" aria-label="PNET Shape Scanner first action">
        <div class="shape-product-card">
          <b>Guest path</b>
          <strong>Open scanner, inspect PNET, copy a safe update.</strong>
          <p>
            The first useful action is not connecting a wallet. It is understanding what public PNET evidence exists and what still needs review.
          </p>
          <div class="shape-user-path" aria-label="PNET Shape Scanner user path">
            <div class="shape-user-path-step">
              <em>1</em>
              <div>
                <span>Read PNET status</span>
                <small>Confirm ASA identity, preview activity, and see scanner safety mode.</small>
              </div>
            </div>
            <div class="shape-user-path-step">
              <em>2</em>
              <div>
                <span>Inspect a signal</span>
                <small>Pick swaps, holder roles, pool context, or a wallet address.</small>
              </div>
            </div>
            <div class="shape-user-path-step">
              <em>3</em>
              <div>
                <span>Share evidence</span>
                <small>Copy a transparency note with boundaries instead of a trade call.</small>
              </div>
            </div>
          </div>
        </div>
        <div class="shape-recent-card" aria-label="Recent PNET scanner rows">
          <div class="shape-recent-head">
            <div>
              <b>Recent PNET rows</b>
              <span>Preview rows mirror the market-scanner shape: direction, amount, time, and evidence state. Live rows remain gated.</span>
            </div>
            <div class="shape-recent-state">preview data</div>
          </div>
          <div class="shape-recent-list">
            <div class="shape-recent-row">
              <span class="shape-recent-type sell">Sell</span>
              <span class="shape-recent-route">4,777 PNET <small>-></small> 0.32 ALGO</span>
              <span class="shape-recent-time">sample</span>
            </div>
            <div class="shape-recent-row">
              <span class="shape-recent-type buy">Buy</span>
              <span class="shape-recent-route">ALGO <small>-></small> PNET</span>
              <span class="shape-recent-time">sample</span>
            </div>
            <div class="shape-recent-row">
              <span class="shape-recent-type">Pool</span>
              <span class="shape-recent-route">PNET / ALGO liquidity watch</span>
              <span class="shape-recent-time">read-only</span>
            </div>
          </div>
        </div>
      </div>
      <div class="shape-next-actions" aria-label="PNET Shape Scanner next actions">
        <div class="shape-next-action">
          <b>Scan PNET first</b>
          <span>PNET remains visible even when there is no opportunity, because the product is a transparency scanner.</span>
        </div>
        <div class="shape-next-action">
          <b>Compare public evidence</b>
          <span>Use Vestige, explorer links, holder notes, and pool context before writing public updates.</span>
        </div>
        <div class="shape-next-action">
          <b>Do not trade from here</b>
          <span>No route execution, no buy/sell advice, no wallet prompt, and no admin controls for guests.</span>
        </div>
      </div>
      <div class="shape-start-strip" aria-label="Start here PNET scan path">
        <div class="shape-start-step">
          <em>1</em>
          <b>Start with PNET</b>
          <span>Confirm ASA 3169177585 and the read-only safety status before reviewing any market context.</span>
        </div>
        <div class="shape-start-step">
          <em>2</em>
          <b>Inspect one signal</b>
          <span>Choose holder concentration, wallet role, pool context, or sample swap activity. Do one thing at a time.</span>
        </div>
        <div class="shape-start-step">
          <em>3</em>
          <b>Copy a safe note</b>
          <span>Export a transparency summary with evidence links and boundaries, not a trading instruction.</span>
        </div>
      </div>
      <div class="shape-dashboard-grid" aria-label="PNET scanner overview">
        <div class="shape-dashboard-card">
          <b>Asset lens</b>
          <strong>PNET · ASA 3169177585</strong>
          <span>The default target stays PNET so the scanner feels specific, not generic.</span>
        </div>
        <div class="shape-dashboard-card">
          <b>Activity feed</b>
          <strong>Swaps previewed</strong>
          <span>Rows show the intended swap-feed shape while live data remains gated.</span>
        </div>
        <div class="shape-dashboard-card">
          <b>Pool context</b>
          <strong>PNET / ALGO watch</strong>
          <span>Liquidity notes stay educational and read-only; no LP deposit prompt.</span>
        </div>
        <div class="shape-dashboard-card">
          <b>Safety mode</b>
          <strong>Scanner only</strong>
          <span>No signing, no trade route, no transaction submission, no admin controls.</span>
        </div>
      </div>
      <div class="shape-signal-deck" aria-label="PNET signal cards">
        <div class="shape-signal-card">
          <b>What should I inspect now?</b>
          <strong>Liquidity shape</strong>
          <span>Use this when a guest wants to understand whether PNET has enough visible pool context for a public update.</span>
          <ul>
            <li>Check PNET / ALGO pool notes and stale-liquidity warnings.</li>
            <li>Open evidence links before saying anything public.</li>
            <li>Do not show LP deposit or buy/sell instructions.</li>
          </ul>
          <div class="shape-signal-status">Status: read-only context</div>
        </div>
        <div class="shape-signal-card">
          <b>Why does it matter?</b>
          <strong>Holder shape</strong>
          <span>Use this when the question is concentration, wallet role, or whether a wallet should be described cautiously.</span>
          <ul>
            <li>Review top-holder share and wallet-role labels.</li>
            <li>Label unknown wallets as unknown until verified.</li>
            <li>Do not infer identity or intent from an address alone.</li>
          </ul>
          <div class="shape-signal-status">Status: manual review</div>
        </div>
        <div class="shape-signal-card">
          <b>What can I share?</b>
          <strong>Shareable signal</strong>
          <span>Use this when a guest wants a public-safe update that keeps PNET visible without hype or trade calls.</span>
          <ul>
            <li>Copy asset, holder, pool, and evidence-boundary notes.</li>
            <li>Say what was checked and what remains unknown.</li>
            <li>Keep price, profit, and investment claims out.</li>
          </ul>
          <div class="shape-signal-status">Status: copy-safe summary</div>
        </div>
      </div>
      <div class="shape-daily-scanner" aria-label="Daily PNET scanner workflow">
        <div class="shape-daily-panel">
          <b>Daily scanner routine</b>
          <strong>Check PNET first, then decide what evidence is worth sharing.</strong>
          <ul>
            <li>Look for PNET swap activity, LP depth notes, and holder-role changes.</li>
            <li>Open public evidence links before posting updates or screenshots.</li>
            <li>Share context and boundaries; do not turn scanner rows into buy/sell calls.</li>
          </ul>
        </div>
        <div class="shape-daily-panel">
          <b>PNET activity shape</b>
          <strong>Example rows people should recognize immediately.</strong>
          <div class="shape-scanner-feed" aria-label="Preview PNET feed rows">
            <div class="shape-scanner-feed-row">
              <span class="shape-scanner-feed-type">Swap</span>
              <span class="shape-scanner-feed-route">PNET → ALGO</span>
              <span class="shape-scanner-feed-state">preview</span>
            </div>
            <div class="shape-scanner-feed-row">
              <span class="shape-scanner-feed-type">Pool</span>
              <span class="shape-scanner-feed-route">PNET / ALGO liquidity watch</span>
              <span class="shape-scanner-feed-state">read-only</span>
            </div>
            <div class="shape-scanner-feed-row">
              <span class="shape-scanner-feed-type">Wallet</span>
              <span class="shape-scanner-feed-route">holder role needs review</span>
              <span class="shape-scanner-feed-state">manual</span>
            </div>
          </div>
        </div>
      </div>
      <div class="shape-scanner-board" aria-label="PNET scanner board">
        <div class="shape-scanner-board-head">
          <div>
            <b>PNET scanner board</b>
            <span>Make the page feel like a market scanner without making trade calls: list PNET flows, pool checks, wallet signals, and evidence status in one place.</span>
          </div>
          <div class="shape-scanner-board-state">sample rows / no live route</div>
        </div>
        <div class="shape-scanner-board-body">
          <div class="shape-scanner-board-row">
            <span class="shape-board-kind">Flow</span>
            <span class="shape-board-route">4,777 PNET → 0.32 ALGO</span>
            <span class="shape-board-note">Recent-swap shape for scanner UX; verify against live public APIs before posting.</span>
            <span class="shape-board-evidence">needs API QA</span>
          </div>
          <div class="shape-scanner-board-row">
            <span class="shape-board-kind">Flow</span>
            <span class="shape-board-route">ALGO → PNET</span>
            <span class="shape-board-note">Direction is context only. No buy/sell button, no route execution, no wallet prompt.</span>
            <span class="shape-board-evidence">read-only</span>
          </div>
          <div class="shape-scanner-board-row">
            <span class="shape-board-kind">Pool</span>
            <span class="shape-board-route">PNET / ALGO depth check</span>
            <span class="shape-board-note">Use as LP education and transparency context, not a deposit instruction.</span>
            <span class="shape-board-evidence">manual review</span>
          </div>
          <div class="shape-scanner-board-row">
            <span class="shape-board-kind">Wallet</span>
            <span class="shape-board-route">holder role signal</span>
            <span class="shape-board-note">Classify public roles cautiously: creator, LP, whale, community, or unknown.</span>
            <span class="shape-board-evidence">no identity claim</span>
          </div>
        </div>
      </div>
      <div class="shape-journey-panel" aria-label="PNET scanner guest journey">
        <div class="shape-journey-title">What should a guest do first?</div>
        <div class="shape-journey-copy">
          AlgoShapes should feel like a walkable scanner: read the PNET snapshot, inspect one target,
          check the evidence boundary, then copy a safe update.
        </div>
        <div class="shape-journey-steps">
          <div class="shape-journey-step">
            <b>1. Read snapshot</b>
            <span>Confirm the page is focused on PNET, public data, and read-only review.</span>
          </div>
          <div class="shape-journey-step">
            <b>2. Pick a target</b>
            <span>Scan the PNET ASA, a wallet address, or a pool/app ID.</span>
          </div>
          <div class="shape-journey-step">
            <b>3. Review signals</b>
            <span>Use holder, swap, pool, and manual-review rows as transparency context.</span>
          </div>
          <div class="shape-journey-step">
            <b>4. Share safely</b>
            <span>Copy a public update with links and boundaries, not trading advice.</span>
          </div>
        </div>
      </div>
      <div class="shape-action-strip" aria-label="PNET scanner quick actions">
        <div class="shape-action-card">
          <b>1 · Scan PNET</b>
          <span>Use PNET / ASA 3169177585 as the default lens. Confirm the public asset, then review holder distribution.</span>
        </div>
        <div class="shape-action-card">
          <b>2 · Check a wallet</b>
          <span>Classify wallets as creator, LP, whale, community, or unknown before writing public updates.</span>
        </div>
        <div class="shape-action-card">
          <b>3 · Inspect a pool</b>
          <span>Open read-only market evidence for liquidity context. Do not treat this panel as buy/sell or route advice.</span>
        </div>
      </div>
      <div class="shape-goal-panel" aria-label="AlgoShapeMaps user goal selector">
        <div class="shape-goal-head">
          <b>Pick why you are scanning</b>
          <span>AlgoShapes should answer a real question. Choose a goal first, then scan the asset, wallet, or pool without connecting a wallet.</span>
        </div>
        <div class="shape-goal-body">
          <div class="shape-goal-grid">
            <button class="shape-goal-button" type="button" data-shape-goal="pnet" aria-pressed="true">
              <b>Verify PNET</b>
              <span>Make a public-safe PNET evidence note before sharing the token.</span>
            </button>
            <button class="shape-goal-button" type="button" data-shape-goal="wallet" aria-pressed="false">
              <b>Check wallet role</b>
              <span>Review creator, LP, whale, community, or unknown labels from public evidence.</span>
            </button>
            <button class="shape-goal-button" type="button" data-shape-goal="update" aria-pressed="false">
              <b>Draft update</b>
              <span>Copy a short transparency note for GitHub, Discord, or a community post.</span>
            </button>
          </div>
          <div class="shape-goal-output" data-shape-goal-output></div>
        </div>
      </div>
      <div class="shape-scan-console" aria-label="PNET read-only scanner console">
        <div class="shape-scan-console-head">
          <div>
            <b>Run a read-only shape scan</b>
            <span>Paste a wallet, ASA, or pool/app ID. The current public version classifies the target and gives safe next steps without calling a wallet or submitting anything.</span>
          </div>
          <div class="shape-scan-mode">No wallet connect</div>
        </div>
        <div class="shape-scan-console-body">
          <div class="shape-scan-input-row">
            <input class="shape-scan-input" data-shape-scan-input value="3169177585" aria-label="ShapeMap scan target" placeholder="Paste PNET ASA, wallet address, or pool/app ID" />
            <button class="shape-scan-run" type="button" data-shape-scan-run>Scan target</button>
          </div>
          <div class="shape-preset-row" aria-label="ShapeMap preset scans">
            <span class="shape-preset-label">Presets</span>
            <button class="shape-preset-button" type="button" data-shape-preset="pnet">PNET ASA</button>
            <button class="shape-preset-button" type="button" data-shape-preset="wallet">Wallet</button>
            <button class="shape-preset-button" type="button" data-shape-preset="pool">Pool/App</button>
          </div>
        </div>
        <div class="shape-scan-console-result" data-shape-scan-result></div>
      </div>
      <div class="shape-usage-actions" aria-label="PNET read-only evidence actions">
        <div class="shape-usage-links">
          <a class="shape-usage-link" href="https://vestige.fi/asset/3169177585" target="_blank" rel="noreferrer">Open PNET on Vestige</a>
          <a class="shape-usage-link" href="https://allo.info/asset/3169177585/token" target="_blank" rel="noreferrer">Open PNET explorer</a>
        </div>
        <button class="shape-usage-copy-btn" type="button" data-shape-copy-summary>Copy PNET scan checklist</button>
      </div>
      <div class="shape-scan-brief" aria-label="PNET scan brief">
        <div class="shape-scan-card">
          <b>Asset identity</b>
          <strong>PNET · ASA 3169177585</strong>
          <span>Use the map as a transparency layer around holder distribution, not as a buy or sell signal.</span>
        </div>
        <div class="shape-scan-card">
          <b>Scanner status</b>
          <strong>Read-only public data</strong>
          <span>No wallet connect is required for the ShapeMap scanner; signing and transactions remain gated.</span>
        </div>
        <div class="shape-scan-card">
          <b>Next value layer</b>
          <strong>Swaps, pools, holder deltas</strong>
          <span>Useful live scanner feeds are planned, but stay gated until API QA and redaction review pass.</span>
        </div>
      </div>
      <div class="shape-market-preview" aria-label="PNET market map preview">
        <div class="shape-market-head">
          <div>
            <b>PNET market map preview</b>
            <span>Sample rows show the scanner shape people should expect: PNET activity, pool context, watchlist notes, and safe next actions. These are preview rows until live feeds are approved.</span>
          </div>
          <div class="shape-market-pill">Preview · read-only</div>
        </div>
        <div class="shape-market-body">
          <div class="shape-market-grid">
            <div class="shape-activity-list" aria-label="Sample PNET activity feed">
              <div class="shape-activity-row">
                <div class="shape-activity-type">Swap</div>
                <div class="shape-activity-main">
                  <div class="shape-activity-route">
                    <span class="shape-token-chip"><img src="/profitnet-pro-logo.png" alt="" />4,777 PNET</span>
                    <span>→</span>
                    <span class="shape-token-chip">0.32 ALGO</span>
                  </div>
                  <span class="shape-activity-note">Sample activity row: verify pool, wallet role, and explorer evidence before sharing.</span>
                </div>
                <div class="shape-activity-status">Needs live API QA</div>
              </div>
              <div class="shape-activity-row">
                <div class="shape-activity-type">Pool watch</div>
                <div class="shape-activity-main">
                  <div class="shape-activity-route">
                    <span class="shape-token-chip">ALGO pair</span>
                    <span>↔</span>
                    <span class="shape-token-chip"><img src="/profitnet-pro-logo.png" alt="" />PNET</span>
                  </div>
                  <span class="shape-activity-note">Track LP depth, recent public swaps, and stale-liquidity warnings without giving deposit instructions.</span>
                </div>
                <div class="shape-activity-status">Read-only evidence</div>
              </div>
              <div class="shape-activity-row">
                <div class="shape-activity-type">Holder move</div>
                <div class="shape-activity-main">
                  <div class="shape-activity-route">
                    <span class="shape-token-chip">Wallet role</span>
                    <span>→</span>
                    <span class="shape-token-chip">manual review</span>
                  </div>
                  <span class="shape-activity-note">Flag whale, LP, creator, community, or unknown roles from public data only.</span>
                </div>
                <div class="shape-activity-status">No identity claim</div>
              </div>
            </div>
            <div class="shape-watchlist" aria-label="PNET scanner watchlist">
              <div class="shape-watch-card">
                <b>Default watchlist</b>
                <strong>PNET, ALGO pairs, known public pools</strong>
                <span>PNET stays visible even when there is no opportunity. The product is transparency first, not route execution.</span>
              </div>
              <div class="shape-watch-card">
                <b>LP education</b>
                <strong>Explain pool depth and risk</strong>
                <span>Encourage people to understand liquidity pools by linking evidence and warnings, not by pushing deposits.</span>
              </div>
              <div class="shape-watch-card">
                <b>Guest next step</b>
                <strong>Copy a scanner snapshot</strong>
                <span>Give users a simple public update they can verify: asset, activity, pool context, holder risk, and boundaries.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="shape-legend" aria-label="AlgoShapes visual legend">
        <div class="shape-legend-item">
          <div class="shape-legend-mark asset">A</div>
          <b>Circle = ASA</b>
          <span>Asset identity, supply, metadata, and public explorer evidence.</span>
        </div>
        <div class="shape-legend-item">
          <div class="shape-legend-mark wallet">W</div>
          <b>Square = wallet</b>
          <span>Holder role notes such as creator, LP, whale, community, or unknown.</span>
        </div>
        <div class="shape-legend-item">
          <div class="shape-legend-mark pool"><span>P</span></div>
          <b>Diamond = pool/app</b>
          <span>Read-only liquidity or app context. No route execution or deposit instruction.</span>
        </div>
        <div class="shape-legend-item">
          <div class="shape-legend-mark review"></div>
          <b>Triangle = review</b>
          <span>Manual research needed before a claim should be shared publicly.</span>
        </div>
      </div>
      <div class="shape-report-template" aria-label="Shareable PNET report template">
        <b>Shareable report format</b>
        <pre>PNET ShapeMap report: asset verified, holder concentration reviewed, wallet roles noted, liquidity evidence linked, no trading advice.</pre>
      </div>
      <div class="shape-usage-grid" aria-label="AlgoShapeMaps user workflow">
        <div class="shape-usage-card">
          <strong>Holder map</strong>
          <span>See large, medium, and community wallets by relative size using read-only Algorand Indexer data.</span>
        </div>
        <div class="shape-usage-card">
          <strong>Concentration risk</strong>
          <span>Check top-holder share before public posts, LP research, or transparency updates.</span>
        </div>
        <div class="shape-usage-card">
          <strong>PNET-first workflow</strong>
          <span>PNET is the default scan target; other ASA IDs remain manual comparison inputs.</span>
        </div>
        <div class="shape-usage-card">
          <strong>Snapshot export</strong>
          <span>Export a shareable holder snapshot for GitHub notes, community review, or QA evidence.</span>
        </div>
      </div>
      <div class="shape-usage-flow" aria-label="Guest flow">
        <b>Guest flow:</b> open ShapeMap <span>→</span> scan PNET <span>→</span> check a wallet <span>→</span> inspect a pool <span>→</span> export snapshot.
      </div>
    `;
    return panel;
  }

  function bindPanelActions(panel) {
    const copyButton = panel.querySelector("[data-shape-copy-summary]");
    if (!copyButton || copyButton.dataset.bound === "true") {
      return;
    }

    copyButton.dataset.bound = "true";
    copyButton.addEventListener("click", async () => {
      const selectedReport = panel.querySelector("[data-shape-goal-report]")?.textContent?.trim();
      const summary = [
        "PNET ShapeMap scan checklist",
        "- Asset: PNET (ASA 3169177585)",
        "- Review: holder concentration, top-wallet share, whale/community split",
        "- Check: creator/LP/whale/community/unknown wallet roles when labels are available",
        "- Inspect: read-only pool evidence for liquidity context; no buy/sell or route advice",
        "- Preview: recent activity rows, pool watch notes, and holder moves remain sample/read-only until live API QA passes",
        "- Export: shareable snapshot for GitHub, Discord, or QA notes",
        `- Report: ${selectedReport || "asset verified, holder concentration reviewed, wallet roles noted, liquidity evidence linked"}`,
        "- Boundary: read-only scanner; no signing, transaction submission, buy/sell advice, or live arb route",
      ].join("\\n");

      try {
        await navigator.clipboard.writeText(summary);
        copyButton.textContent = "Checklist copied";
      } catch (error) {
        copyButton.textContent = "Copy unavailable";
      }

      window.setTimeout(() => {
        copyButton.textContent = "Copy PNET scan checklist";
      }, 2400);
    });

    const scanInput = panel.querySelector("[data-shape-scan-input]");
    const scanButton = panel.querySelector("[data-shape-scan-run]");
    const presetButtons = panel.querySelectorAll("[data-shape-preset]");
    const goalButtons = panel.querySelectorAll("[data-shape-goal]");

    if (scanInput && scanButton) {
      scanButton.addEventListener("click", () => renderScanResult(panel, scanInput.value));
      scanInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          renderScanResult(panel, scanInput.value);
        }
      });
    }

    presetButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const value = PRESET_VALUES[button.dataset.shapePreset] || "3169177585";
        if (scanInput) {
          scanInput.value = value;
          scanInput.focus();
          scanInput.select();
        }
        renderScanResult(panel, value);
      });
    });

    goalButtons.forEach((button) => {
      button.addEventListener("click", () => {
        renderGoal(panel, button.dataset.shapeGoal || "pnet");
      });
    });
  }

  function enhanceShapeMap() {
    const page = document.querySelector(".shape-page");
    if (!page || page.querySelector(`[${PANEL_ATTR}]`)) {
      return;
    }

    injectStyle();
    const introCard = page.querySelector(".shape-mailbox-card");
    const panel = createPanel();

    if (introCard && introCard.parentNode) {
      introCard.insertAdjacentElement("afterend", panel);
    } else {
      page.insertAdjacentElement("afterbegin", panel);
    }

    bindPanelActions(panel);
    renderScanResult(panel, "3169177585");
    renderGoal(panel, "pnet");
  }

  function scheduleEnhance() {
    window.requestAnimationFrame(enhanceShapeMap);
  }

  window.addEventListener("hashchange", scheduleEnhance);
  window.addEventListener("popstate", scheduleEnhance);
  document.addEventListener("DOMContentLoaded", scheduleEnhance);

  const observer = new MutationObserver(scheduleEnhance);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  scheduleEnhance();
})();
