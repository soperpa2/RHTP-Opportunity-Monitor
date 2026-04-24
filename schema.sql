:root {
  --ink: #17211c;
  --muted: #5f6f68;
  --green: #1d3a27;
  --ochre: #c66b3d;
  --ivory: #f6f1e8;
  --mist: #dce1e0;
  --white: #ffffff;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, Arial, sans-serif; color: var(--ink); background: var(--ivory); }
header { background: var(--green); color: white; padding: 32px 48px; }
header h1 { margin: 0 0 8px; font-size: 34px; }
header p { margin: 0; color: #e6eee9; }
.cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 24px 48px; }
.card { background: white; border-radius: 18px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,.08); }
.card span { display: block; color: var(--muted); font-size: 14px; }
.card strong { font-size: 32px; }
.panel { padding: 0 48px 16px; }
.filters { background: white; padding: 16px; border-radius: 18px; display: flex; gap: 12px; align-items: end; box-shadow: 0 8px 24px rgba(0,0,0,.06); }
label { display: grid; gap: 6px; color: var(--muted); font-size: 13px; }
select, input { padding: 10px 12px; border: 1px solid var(--mist); border-radius: 10px; min-width: 160px; }
button { background: var(--green); color: white; border: 0; padding: 11px 16px; border-radius: 10px; cursor: pointer; }
main { padding: 0 48px 48px; display: grid; gap: 16px; }
.opportunity, .empty { background: white; border-radius: 18px; padding: 22px; box-shadow: 0 8px 24px rgba(0,0,0,.07); }
.opp-header { display: flex; justify-content: space-between; gap: 20px; }
h2 { margin: 0; font-size: 20px; }
a { color: var(--green); }
.meta { color: var(--muted); margin: 6px 0 0; }
.badge { background: var(--mist); border-radius: 999px; padding: 8px 12px; height: fit-content; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
.tags span { background: #f1e2d9; color: #5c2c1b; padding: 6px 10px; border-radius: 999px; font-size: 12px; }
.review { display: flex; gap: 10px; }
.review input { flex: 1; }
@media (max-width: 900px) {
  .cards { grid-template-columns: 1fr 1fr; }
  header, .cards, .panel, main { padding-left: 20px; padding-right: 20px; }
  .filters, .review { flex-direction: column; align-items: stretch; }
}
