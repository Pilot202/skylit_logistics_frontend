import React from 'react'
import './App.css'
import {useEffect, useState, useRef} from 'react'
import InventoryTable from './components/InventoryTable'
import LiveActivityFeed from './components/LiveActivityFeed'

const sample = [
  {name:'Widget A', sku:'WID-A', stock:24},
  {name:'Widget B', sku:'WID-B', stock:8},
  {name:'Gadget', sku:'GAD-1', stock:3},
]

export default function App(){
  const [items, setItems] = useState(sample)
  const [events, setEvents] = useState([])
  const wsRef = useRef(null)

  useEffect(()=>{
    // fetch initial inventory from backend
    async function loadInventory(){
      try{
        const base = (location.hostname==='localhost')? 'http://localhost:8000':'http://' + location.hostname
        const res = await fetch(base + '/admin/inventory')
        if(res.ok){
          const data = await res.json()
          setItems(data.map(d=>({name:d.product_name||d.sku, sku:d.sku, stock:d.stock})))
          setEvents(e=>[{type:'info',message:'Loaded inventory from backend',ts:Date.now()},...e])
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
            setItems(cur=>cur.map(it=> it.sku===data.sku? {...it, stock:data.stock}: it))
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
          setItems(cur=>{
            if(cur.length===0) return cur
            const copy = [...cur]
            const i = Math.floor(Math.random()*copy.length)
            const change = Math.floor(Math.random()*5)-2
            copy[i] = {...copy[i], stock: Math.max(0, copy[i].stock + change)}
            setEvents(e=>[{type:'mock',message:`${copy[i].sku} stock=${copy[i].stock}`,ts:Date.now()},...e])
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
    <div className="app">
      <header>
        <h1>Admin Dashboard</h1>
      </header>
      <div className="grid">
        <InventoryTable items={items} />
        <LiveActivityFeed events={events} />
      </div>
    </div>
  )
}
