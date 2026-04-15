import React from 'react'

export default function InventoryTable({items, branchName}){
  return (
    <div className="card inventory" style={{marginBottom: '20px'}}>
      <h2>{branchName ? `${branchName} Inventory` : 'Global Inventory'}</h2>
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Seller</th>
            <th>Stock</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((i, idx)=> (
            <tr key={i.sku || idx}>
              <td>{i.name}</td>
              <td>{i.seller}</td>
              <td>{i.stock}</td>
              <td className={i.stock<10? 'low':'ok'}>{i.stock<10? 'Low':'OK'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
