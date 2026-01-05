import React from 'react'

export default function LiveActivityFeed({events}){
  return (
    <div className="card feed">
      <h2>Live Activity</h2>
      <ul>
        {events.slice(0,20).map((e,idx)=> (
          <li key={idx}><span className={`badge ${e.type}`}>{e.type}</span> <strong>{e.message}</strong> <small>{new Date(e.ts).toLocaleTimeString()}</small></li>
        ))}
      </ul>
    </div>
  )
}
