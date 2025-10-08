import React, { useState } from "react";

export default function App() {
  const [location, setLocation] = useState("");
  const [date, setDate] = useState("");
  const [params, setParams] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  function handleSubmit(e) {
    e.preventDefault();
    if (!location || !date) {
      setResult({ error: "Please provide location and date." });
      return;
    }
    setRunning(true);
    setResult(null);

    setTimeout(() => {
      const potential = (Math.random() * 50 + 10).toFixed(1);
      const rooftop = Math.round(40 + Math.random() * 40);
      const facade = Math.round(10 + Math.random() * 50);
      setResult({ potential, rooftop, facade, recommendation: "Consider BIPV" });
      setRunning(false);
    }, 800);
  }

  function handleReset() {
    setLocation("");
    setDate("");
    setParams("");
    setResult(null);
  }

  function downloadCSV() {
    if (!result || result.error) return;
    const rows = [
      ["Location", location],
      ["Date", date],
      ["Estimated kWh/yr", result.potential],
      ["Rooftop potential (%)", result.rooftop],
      ["Facade potential (%)", result.facade],
      ["Recommendation", result.recommendation]
    ];
    const csv = rows
      .map(r => r.map(c => {
        const escaped = String(c).replace(/"/g, '""');
        return `"${escaped}"`;
      }).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bipv-report.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <style>{`
        body { background: #f8fafc; color: #1e293b; font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .container { max-width: 1100px; margin: auto; padding: 20px; }
        header { margin-bottom: 20px; }
        header h1 { font-size: 24px; font-weight: bold; }
        main { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }
        .inputs, .viewer { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .inputs label { display: block; margin-top: 10px; }
        .inputs input { width: 100%; padding: 6px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; }
        .buttons { margin-top: 10px; display: flex; gap: 10px; }
        button { padding: 8px 12px; border: none; border-radius: 5px; cursor: pointer; }
        .run { background-color: #059669; color: white; }
        .reset { background-color: #e2e8f0; }
        .viewer-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .viewer-box { background: #f1f5f9; display: flex; align-items: center; justify-content: center; height: 200px; color: #64748b; border-radius: 8px; text-align: center; }
        .summary-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 14px; }
        .dashboard { margin-top: 10px; border: 1px solid #e2e8f0; padding: 10px; border-radius: 8px; background: #fff; }
        footer { font-size: 12px; color: #64748b; text-align: center; margin-top: 20px; }
        .error { color: #b91c1c; }
      `}</style>

      <div className="container">
        <header>
          <h1>Saurya Sankulan — BIPV Assessment (Prototype)</h1>
          <p>location/date → simulate shadows & irradiance → view results.</p>
        </header>

        <main>
          <section className="inputs">
            <h2>Inputs</h2>
            <form onSubmit={handleSubmit}>
              <label htmlFor="location">Location</label>
              <input id="location" type="text" value={location} onChange={e => setLocation(e.target.value)} placeholder="City, coordinates, or address" required />

              <label htmlFor="date">Date</label>
              <input id="date" type="date" value={date} onChange={e => setDate(e.target.value)} required />

              <label htmlFor="params">Other Params (optional)</label>
              <input id="params" type="text" value={params} onChange={e => setParams(e.target.value)} placeholder="GHI, tilt, etc." />

              <div className="buttons">
                <button type="submit" className="run" disabled={running}>{running ? 'Simulating...' : 'Run Simulation'}</button>
                <button type="button" className="reset" onClick={handleReset}>Reset</button>
              </div>
            </form>

            <hr />
            <h3>Notes</h3>
          </section>

          <section className="viewer">
            <h2>Viewer & Visualization</h2>
            <div className="viewer-grid">
              <div className="viewer-box" id="viewer">
                <div>
                  3D Model Viewer
                  <br />
                  <small>(placeholder for 3d model)</small>
                </div>
              </div>

              <div className="summary-box">
                <h3>Simulation Summary</h3>
                <div>
                  {result && result.error ? (
                    <div className="error">{result.error}</div>
                  ) : result ? (
                    <div>
                      <p>Total estimated potential: <strong>{result.potential} kWh/yr</strong></p>
                      <p>Rooftop: <strong>{result.rooftop}%</strong></p>
                      <p>Façade: <strong>{result.facade}%</strong></p>
                      <p>Recommendation: {result.recommendation}</p>
                      <div style={{ marginTop: 10 }}>
                        <button onClick={downloadCSV}>Download CSV</button>
                      </div>
                    </div>
                  ) : (
                    <div id="summary">placeholder for shadow & sunlight coverage results</div>
                  )}
                </div>
              </div>
            </div>

            <h3>Dashboard</h3>
            <div className="dashboard">Shadow Coverage here</div>
          </section>
        </main>

        <footer> • Saurya Sankulan Mini Project</footer>
      </div>
    </>
  );
}