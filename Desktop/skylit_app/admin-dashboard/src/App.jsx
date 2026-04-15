import React from 'react'
import './App.css'
import {useEffect, useState, useRef} from 'react'
import InventoryTable from './components/InventoryTable'
import LiveActivityFeed from './components/LiveActivityFeed'
import Analytics from './components/Analytics'
import StockOperations from './components/StockOperations'

const sample = [
  {name:'Widget A', seller:'Acme Corp', stock:24},
  {name:'Widget B', seller:'TechSupply Inc', stock:8},
  {name:'Gadget', seller:'Global Traders', stock:3},
]

export default function App(){
  const [branchInventories, setBranchInventories] = useState([])
  const [events, setEvents] = useState([])
  const [currentView, setCurrentView] = useState('overview')
  const wsRef = useRef(null)

  useEffect(()=>{
    // fetch initial inventory from backend
    async function loadInventory(){
      try{
        const base = (location.hostname==='localhost')? 'http://localhost:8000':'http://' + location.hostname
        const res = await fetch(base + '/admin/branches-inventory')
        if(res.ok){
          const data = await res.json()
          setBranchInventories(data)
          setEvents(e=>[{type:'info',message:'Loaded branch inventories from backend',ts:Date.now()},...e])
        }
      }catch(err){
        setEvents(e=>[{type:'error',message:'Failed to load inventory',ts:Date.now()},...e])
      }
    }
    loadInventory()

    // connect to backend websocket at /ws/dashboard
    const wsUrl = (location.hostname==='localhost')? 'ws://localhost:8000/ws/dashboard':'ws://' + location.hostname + '/ws/dashboard'
    let ws
    try{
      ws = new WebSocket(wsUrl)
      ws.onopen = ()=> setEvents(e=>[{type:'info',message:'Connected to real-time backend',ts:Date.now()},...e])
      ws.onmessage = (m)=>{
        try{
          const data = JSON.parse(m.data)
          // backend broadcasts {sku, stock, seller, action}
          if(data.sku){
            // Instead of trying to patch nested states, simply trigger a fresh reload
            // of the branch inventories to ensure perfect sync
            loadInventory();
            setEvents(e=>[{type:'update',message:`${data.sku} ${data.action||'update'} stock=${data.stock}`,ts:Date.now()},...e])
          } else {
            setEvents(e=>[{type:'event',message: JSON.stringify(data),ts:Date.now()},...e])
          }
        }catch(err){
          console.error('ws parse',err)
        }
      }
      ws.onerror = ()=> setEvents(e=>[{type:'error',message:'WebSocket error',ts:Date.now()},...e])
      ws.onclose = ()=> setEvents(e=>[{type:'info',message:'WebSocket closed',ts:Date.now()},...e])
      wsRef.current = ws
    }catch(err){
      setEvents(e=>[{type:'error',message:'WebSocket connection failed',ts:Date.now()},...e])
    }

    // fallback mock updates if ws not open within 3s
    const fallback = setTimeout(()=>{
      if(!ws || ws.readyState !== WebSocket.OPEN){
        const t = setInterval(()=>{
          setBranchInventories(cur=>{
            if(cur.length===0) return cur
            const copy = JSON.parse(JSON.stringify(cur))
            const bIdx = Math.floor(Math.random()*copy.length)
            if(copy[bIdx].items.length > 0){
              const i = Math.floor(Math.random()*copy[bIdx].items.length)
              const change = Math.floor(Math.random()*5)-2
              copy[bIdx].items[i].stock = Math.max(0, copy[bIdx].items[i].stock + change)
              setEvents(e=>[{type:'mock',message:`${copy[bIdx].items[i].name} stock updated dynamically`,ts:Date.now()},...e])
            }
            return copy
          })
        },5000)
        wsRef.current = {close: ()=> clearInterval(t)}
      }
    },3000)

    return ()=>{
      clearTimeout(fallback)
      if(wsRef.current) wsRef.current.close()
    }
  },[])

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">SKYLIT DASHBOARD</div>
        <button 
          className={`nav-item ${currentView === 'overview' ? 'active' : ''}`}
          onClick={() => setCurrentView('overview')}
        >
          Live Overview
        </button>
        <button 
          className={`nav-item ${currentView === 'analytics' ? 'active' : ''}`}
          onClick={() => setCurrentView('analytics')}
        >
          Analytics & Enquiries
        </button>
        <button 
          className={`nav-item ${currentView === 'operations' ? 'active' : ''}`}
          onClick={() => setCurrentView('operations')}
        >
          Stock Operations
        </button>
      </aside>

      <main className="main-content">
        {currentView === 'overview' && (
          <div className="fade-in">
            <h2 className="card-title" style={{fontSize: '28px', color: '#fff', marginBottom: '8px'}}>Real-Time Operations</h2>
            <p style={{color: 'var(--text-muted)', marginBottom: '24px'}}>Live view of active warehouse operations and global inventory levels.</p>
            <div className="grid-overview">
              <div className="pane-glass p-0 flex flex-col gap-4 max-h-[80vh] overflow-y-auto">
                {branchInventories.map(b => (
                   <InventoryTable key={b.branch_name} branchName={b.branch_name} items={b.items} />
                ))}
                {branchInventories.length === 0 && (
                   <div style={{padding: '2rem', textAlign: 'center'}}>No branches found...</div>
                )}
              </div>
              <div className="pane-glass">
                <LiveActivityFeed events={events} />
              </div>
            </div>
          </div>
        )}

        {currentView === 'analytics' && (
          <Analytics />
        )}

        {currentView === 'operations' && (
          <StockOperations />
        )}
      </main>
    </div>
  )
}
