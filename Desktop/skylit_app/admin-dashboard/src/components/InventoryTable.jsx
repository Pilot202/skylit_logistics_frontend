import React from 'react'

export default function InventoryTable({items}){
  return (
    <div className="card inventory">
      <h2>Inventory</h2>
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th>SKU</th>
            <th>Stock</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map(i=> (
            <tr key={i.sku}>
              <td>{i.name}</td>
              <td>{i.sku}</td>
              <td>{i.stock}</td>
              <td className={i.stock<10? 'low':'ok'}>{i.stock<10? 'Low':'OK'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
