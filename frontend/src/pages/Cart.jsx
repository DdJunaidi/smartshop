import { useEffect, useState } from "react";
import { getCart, updateCartItem, checkout } from "../api";

export default function Cart() {
  const [cart, setCart] = useState(null);
  const [err, setErr] = useState("");

  async function load() {
    try {
      const r = await getCart();
      setCart(r.data);
    } catch {
      setErr("Please login to view your cart.");
    }
  }
  useEffect(() => { load(); }, []);

  async function changeQty(itemId, qty) {
    await updateCartItem(itemId, qty);
    load();
  }
  async function doCheckout() {
    try {
      const r = await checkout();
      alert(`Order placed. Total: $${r.data.total}`);
      load();
    } catch (e) {
      alert("Checkout failed");
    }
  }

  if (err) return <p style={{ color:"tomato" }}>{err}</p>;
  if (!cart) return <p>Loading cart…</p>;

  const total = cart.items.reduce((sum, it) => sum + Number(it.product_detail.price) * it.qty, 0);

  return (
    <div>
      <h3>Your Cart</h3>
      {!cart.items.length ? <p>Cart is empty.</p> : (
        <div>
          {cart.items.map(it => (
            <div key={it.id} style={{ display:"flex", gap:8, alignItems:"center", marginBottom:8 }}>
              <img src={it.product_detail.image_url} alt="" style={{ width:64, height:64, objectFit:"cover", borderRadius:8 }} />
              <div style={{ flex:1 }}>
                <div><strong>{it.product_detail.name}</strong></div>
                <div>${Number(it.product_detail.price).toFixed(2)}</div>
              </div>
              <input type="number" min={0} value={it.qty}
                     onChange={e=>changeQty(it.id, Number(e.target.value))}
                     style={{ width:70 }} />
            </div>
          ))}
          <hr />
          <div style={{ display:"flex", justifyContent:"space-between" }}>
            <strong>Total</strong>
            <strong>${total.toFixed(2)}</strong>
          </div>
          <button onClick={doCheckout} style={{ marginTop:12 }}>Checkout</button>
        </div>
      )}
    </div>
  );
}
