import React, { useState, useEffect, useMemo } from 'react';
import './Analytics.css';

export default function Analytics() {
  const [data, setData] = useState({ products: [], sellers: [], transactions: [], summary: {} });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('products');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const base = (location.hostname === 'localhost') ? 'http://localhost:8000' : 'http://' + location.hostname;
        const res = await fetch(base + '/admin/analytics');
        if (res.ok) {
          const json = await res.json();
          setData({
            products: json.products || [],
            sellers: json.sellers || [],
            transactions: json.transactions || [],
            summary: json.summary || {}
          });
        }
      } catch (err) {
        console.error("Failed to load analytics", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, []);

  const downloadCSV = (filename, rows) => {
    if (!rows || !rows.length) return;
    const headers = Object.keys(rows[0]).join(',');
    const csvData = rows.map(r => 
      Object.values(r).map(val => {
        if (val === null || val === undefined) return '""';
        const str = String(val);
        return str.includes(',') ? `"${str}"` : str;
      }).join(',')
    ).join('\n');

    const blob = new Blob([`${headers}\n${csvData}`], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const filteredData = useMemo(() => {
    if (!searchTerm) return data[activeTab] || [];
    const lower = searchTerm.toLowerCase();
    return (data[activeTab] || []).filter(item => 
      Object.values(item).some(val => val && String(val).toLowerCase().includes(lower))
    );
  }, [data, activeTab, searchTerm]);

  if (loading) return <div className="loading">Gathering Intelligence...</div>;

  return (
    <div className="analytics-module">
      <div className="analytics-header">
        <h2>Intelligence & Reporting</h2>
        <div className="summary-cards">
            <div className="summary-card">
              <span className="sc-label">Total Products</span>
              <span className="sc-value">{data.summary.total_products || 0}</span>
            </div>
            <div className="summary-card">
              <span className="sc-label">Global Stock</span>
              <span className="sc-value">{data.summary.total_stock || 0}</span>
            </div>
            <div className="summary-card">
              <span className="sc-label">Registered Sellers</span>
              <span className="sc-value">{data.summary.total_sellers || 0}</span>
            </div>
             <div className="summary-card">
              <span className="sc-label">Total Transactions</span>
              <span className="sc-value">{data.summary.total_transactions || 0}</span>
            </div>
        </div>
      </div>

      <div className="analytics-body pane-glass">
        <div className="controls">
          <div className="tab-group">
            <button className={`tab ${activeTab === 'products' ? 'active' : ''}`} onClick={() => setActiveTab('products')}>Products</button>
            <button className={`tab ${activeTab === 'sellers' ? 'active' : ''}`} onClick={() => setActiveTab('sellers')}>Sellers</button>
            <button className={`tab ${activeTab === 'transactions' ? 'active' : ''}`} onClick={() => setActiveTab('transactions')}>Transactions / Buyers</button>
          </div>
          <div className="actions">
            <input 
              type="text" 
              className="search-input" 
              placeholder={`Search ${activeTab}...`} 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
            <button className="btn-download" onClick={() => downloadCSV(`skylit_${activeTab}_report`, filteredData)}>
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export CSV
            </button>
          </div>
        </div>

        <div className="table-responsive">
          {filteredData.length === 0 ? (
            <div className="empty-state">No data available to display.</div>
          ) : (
            <table className="dt-table">
              <thead>
                <tr>
                  {Object.keys(filteredData[0])
                    .filter(key => key !== 'id' && key !== 'sku')
                    .map(key => (
                    <th key={key}>{key.toUpperCase()}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredData.map((row, idx) => (
                  <tr key={idx} style={{ animationDelay: `${idx * 0.05}s` }}>
                    {Object.entries(row)
                      .filter(([key]) => key !== 'id' && key !== 'sku')
                      .map(([key, val], cellIdx) => (
                      <td key={cellIdx}>{val === null || val === undefined ? '—' : String(val)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
