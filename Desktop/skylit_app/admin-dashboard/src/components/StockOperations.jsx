import React, { useState, useEffect } from 'react';
import './StockOperations.css';

export default function StockOperations() {
  const [activeTab, setActiveTab] = useState('add');
  const [branches, setBranches] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Form states
  const [selectedBranch, setSelectedBranch] = useState('');
  const [targetBranch, setTargetBranch] = useState(''); // for moving
  const [selectedSku, setSelectedSku] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [destination, setDestination] = useState(''); // for removing/shipping
  
  // Branch stock state
  const [branchStocks, setBranchStocks] = useState(null);
  const [selectedBranchForStock, setSelectedBranchForStock] = useState('');

  const baseUrl = (location.hostname === 'localhost') ? 'http://localhost:8000' : 'http://' + location.hostname;

  useEffect(() => {
    async function fetchData() {
      try {
        const [branchRes, prodRes] = await Promise.all([
          fetch(`${baseUrl}/api/branches`),
          fetch(`${baseUrl}/admin/analytics`)
        ]);
        
        if (branchRes.ok && prodRes.ok) {
          const bData = await branchRes.json();
          const pData = await prodRes.json();
          setBranches(bData);
          setProducts(pData.products || []);
          if (bData.length > 0) {
            setSelectedBranch(bData[0].name);
            setTargetBranch(bData[1]?.name || bData[0].name);
            setSelectedBranchForStock(bData[0].name);
          }
          if (pData.products?.length > 0) {
            setSelectedSku(pData.products[0].sku);
          }
        }
      } catch (err) {
        console.error("Failed to load foundational data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [baseUrl]);

  useEffect(() => {
    if (activeTab === 'check' && selectedBranchForStock) {
      loadBranchStock(selectedBranchForStock);
    }
  }, [activeTab, selectedBranchForStock]);

  const loadBranchStock = async (branchName) => {
    try {
      const res = await fetch(`${baseUrl}/api/branches/${branchName}/report`);
      if (res.ok) {
        const data = await res.json();
        setBranchStocks(data.inventory.products || []);
      } else {
        setBranchStocks([]);
      }
    } catch (err) {
      console.error(err);
      setBranchStocks([]);
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 4000);
  };

  const handleAction = async (e) => {
    e.preventDefault();
    if (!selectedBranch || !selectedSku || quantity <= 0) {
      return showMessage('error', 'Please fill all required fields correctly.');
    }
    
    // Safety check - we shouldn't attempt to ship out from or move from "all"
    if ((activeTab === 'remove' || activeTab === 'move') && selectedBranch === 'all') {
      return showMessage('error', 'Cannot ship out or distribute from multiple branches at once. Select a specific origin branch.');
    }

    let url = '';
    let payload = {};

    try {
      if (activeTab === 'add') {
        url = `${baseUrl}/api/branches/${selectedBranch}/add-stock`;
        payload = { branch_name: selectedBranch, product_sku: selectedSku, quantity: parseInt(quantity) };
      } else if (activeTab === 'remove') {
        if (!destination) return showMessage('error', 'Destination is required for removal/shipping.');
        url = `${baseUrl}/api/branches/${selectedBranch}/ship-out`;
        payload = { branch_name: selectedBranch, product_sku: selectedSku, quantity: parseInt(quantity), destination };
      } else if (activeTab === 'move') {
        if (selectedBranch === targetBranch) return showMessage('error', 'Source and target branches must be different.');
        url = `${baseUrl}/api/transfers/initiate`;
        payload = { from_branch: selectedBranch, to_branch: targetBranch, product_sku: selectedSku, quantity: parseInt(quantity) };
      }

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        showMessage('success', `Operation successful for ${selectedSku}!`);
        setQuantity(1);
        setDestination('');
      } else {
        const errData = await res.json();
        showMessage('error', errData.detail || 'Operation failed.');
      }
    } catch (err) {
      console.error(err);
      showMessage('error', 'Network or system error.');
    }
  };

  if (loading) return <div className="loading">Loading Operations...</div>;

  return (
    <div className="operations-module">
      <div className="op-header">
        <h2>Stock Operations</h2>
      </div>

      <div className="op-tabs">
        <button className={`op-tab ${activeTab === 'add' ? 'active' : ''}`} onClick={() => setActiveTab('add')}>Add Stock</button>
        <button className={`op-tab ${activeTab === 'remove' ? 'active' : ''}`} onClick={() => setActiveTab('remove')}>Remove/Ship</button>
        <button className={`op-tab ${activeTab === 'move' ? 'active' : ''}`} onClick={() => setActiveTab('move')}>Move Stock</button>
        <button className={`op-tab ${activeTab === 'check' ? 'active' : ''}`} onClick={() => setActiveTab('check')}>Check Branch Stocks</button>
      </div>

      <div className="pane-glass op-body fade-in">
        {message.text && (
          <div className={`op-alert alert-${message.type}`}>
            {message.type === 'success' ? '✅' : '❌'} {message.text}
          </div>
        )}

        {(activeTab === 'add' || activeTab === 'remove' || activeTab === 'move') && (
          <form className="op-form" onSubmit={handleAction}>
            <div className="form-group">
              <label>{activeTab === 'add' ? 'Target Branch' : 'Source Branch'}</label>
              <select value={selectedBranch} onChange={e => setSelectedBranch(e.target.value)}>
                {activeTab === 'add' && <option value="all">🌐 All Branches</option>}
                {branches.map(b => <option key={b.id} value={b.name}>{b.name}</option>)}
              </select>
            </div>

            {activeTab === 'move' && (
              <div className="form-group">
                <label>Target Branch</label>
                <select value={targetBranch} onChange={e => setTargetBranch(e.target.value)}>
                  {branches.map(b => <option key={b.id} value={b.name}>{b.name}</option>)}
                </select>
              </div>
            )}

            <div className="form-group">
              <label>Product (SKU) — Select or Type New</label>
              <input 
                list="sku-options" 
                value={selectedSku} 
                onChange={e => setSelectedSku(e.target.value)} 
                placeholder="Select existing or type new SKU..." 
                required 
              />
              <datalist id="sku-options">
                {products.map(p => <option key={p.id} value={p.sku}>{p.name} ({p.sku})</option>)}
              </datalist>
            </div>

            <div className="form-group">
              <label>Quantity</label>
              <input type="number" min="1" value={quantity} onChange={e => setQuantity(e.target.value)} />
            </div>

            {activeTab === 'remove' && (
              <div className="form-group">
                <label>Destination / Buyer</label>
                <input type="text" placeholder="e.g. Lagos Warehouse, Retail Customer" value={destination} onChange={e => setDestination(e.target.value)} />
              </div>
            )}

            <button type="submit" className="op-submit-btn">
              {activeTab === 'add' && 'Add Inventory'}
              {activeTab === 'remove' && 'Dispatch Stock'}
              {activeTab === 'move' && 'Initiate Transfer'}
            </button>
          </form>
        )}

        {activeTab === 'check' && (
          <div className="op-check">
            <div className="check-controls">
              <label>Select Branch to View:</label>
              <select value={selectedBranchForStock} onChange={e => setSelectedBranchForStock(e.target.value)}>
                {branches.map(b => <option key={b.id} value={b.name}>{b.name} ({b.location})</option>)}
              </select>
            </div>
            
            <div className="table-responsive" style={{marginTop: '20px'}}>
              {branchStocks === null ? (
                <div>Loading...</div>
              ) : branchStocks.length === 0 ? (
                <div className="empty-state">No inventory physically present in this branch.</div>
              ) : (
                <table className="dt-table">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Seller</th>
                      <th>Quantity in Branch</th>
                      <th>Minimum Threshold</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {branchStocks.map((item, idx) => (
                      <tr key={idx} style={{animationDelay: `${idx*0.05}s`}}>
                        <td>{item.name}</td>
                        <td>{item.seller}</td>
                        <td style={{fontWeight: 'bold', color: item.stock <= item.min_level ? 'var(--danger)' : 'var(--success)'}}>{item.stock}</td>
                        <td>{item.min_level}</td>
                        <td>{item.stock <= item.min_level ? '⚠️ Low Stock' : '✅ Healthy'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
