"use client";

import { useState, useEffect } from "react";

// The hardcoded catalog matching the backend so we can render the image/details
const LOCAL_CATALOG = {
  "item_101": { name: "Sony WH-1000XM5 Wireless Headphones", price: 29990, emoji: "🎧" },
  "item_102": { name: "Apple 20W USB-C Power Adapter", price: 1900, emoji: "🔌" },
  "item_201": { name: "L'Oreal Paris Revitalift Serum", price: 999, emoji: "🧴" },
  "item_202": { name: "Gillette Mach3 Turbo Razor", price: 350, emoji: "🪒" },
  "item_301": { name: "Pedigree Adult Dry Dog Food 3kg", price: 700, emoji: "🐕" },
  "item_401": { name: "UNO Card Game", price: 149, emoji: "🃏" },
  "item_402": { name: "Hot Wheels Diecast Car", price: 179, emoji: "🏎️" },
  "item_501": { name: "Duracell AA Batteries (4 Pack)", price: 170, emoji: "🔋" },
  "item_601": { name: "Durex Mutual Climax Condoms", price: 350, emoji: "🌙" },
};

export default function CartPage() {
  const [cart] = useState([
    { id: 1, name: "Amul Taaza Toned Milk (1L)", price: 72, emoji: "🥛" },
    { id: 2, name: "Harvest Gold White Bread", price: 50, emoji: "🍞" },
    { id: 3, name: "Farm Fresh Eggs (6 Pack)", price: 65, emoji: "🥚" }
  ]);
  
  const [loading, setLoading] = useState(true);
  const [recommendationText, setRecommendationText] = useState("");
  const [recommendedItemId, setRecommendedItemId] = useState("");
  const [error, setError] = useState(false);

  useEffect(() => {
    async function fetchRecommendation() {
      try {
        // Same-origin by default: the recommender runs as a Next.js route handler
        // at /api/recommend, so there is no cross-origin request and no CORS to
        // configure. Set NEXT_PUBLIC_API_URL only when pointing at a separately
        // hosted backend (e.g. the FastAPI service in mvp/api).
        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";

        const now = new Date();
        const timeOfDay = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dayOfWeek = now.toLocaleDateString('en-US', { weekday: 'long' });

        // Hard client-side deadline. When both LLM free tiers are quota-exhausted
        // the upstream call can stall rather than error, which would leave the
        // cart spinning indefinitely. Failing fast here drops us into the
        // degraded suggestion below instead (M9).
        const res = await fetch(`${apiUrl}/api/recommend`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            items: cart.map(item => item.name),
            time_of_day: timeOfDay,
            day_of_week: dayOfWeek
          }),
          signal: AbortSignal.timeout(15000)
        });

        if (!res.ok) throw new Error("API failed");
        
        if (!res.body) throw new Error("No body");
        
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullText = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          fullText += decoder.decode(value, { stream: true });
          
          // Try to split the rationale and the item_id if we have the delimiter
          if (fullText.includes("|||")) {
            const parts = fullText.split("|||");
            setRecommendationText(parts[0]);
            if (parts[1] && parts[1].trim()) {
                setRecommendedItemId(parts[1].trim());
            }
          } else {
            setRecommendationText(fullText);
          }
        }
      } catch (err) {
        console.error("Recommendation error:", err);
        setError(true);
        // Fallback degraded mode for the UI if completely offline
        setRecommendationText("Having a busy day? Maybe you need something else.");
        setRecommendedItemId("item_501");
      } finally {
        setLoading(false);
      }
    }

    fetchRecommendation();
  }, [cart]);

  const cartTotal = cart.reduce((acc, item) => acc + item.price, 0);
  const recommendedItem = LOCAL_CATALOG[recommendedItemId as keyof typeof LOCAL_CATALOG];

  return (
    <main className="min-h-screen bg-gray-50 flex justify-center text-black">
      <div className="w-full max-w-md bg-white shadow-xl relative min-h-screen overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-yellow-400 p-4 font-bold text-lg flex items-center justify-between sticky top-0 z-10 shadow-sm">
          <span>Checkout</span>
          <span className="text-sm bg-white px-2 py-1 rounded-md text-black">10 MINS</span>
        </div>

        {/* Content */}
        <div className="flex-1 p-4 overflow-y-auto pb-24 space-y-6">
          
          {/* Main Cart */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <h2 className="font-bold text-gray-800 mb-4 text-sm uppercase tracking-wide">Review Items</h2>
            <div className="space-y-4">
              {cart.map((item) => (
                <div key={item.id} className="flex justify-between items-center border-b border-gray-50 pb-3 last:border-0 last:pb-0">
                  <div className="flex items-center gap-3">
                    <div className="text-3xl bg-gray-50 p-2 rounded-lg">{item.emoji}</div>
                    <div className="font-medium text-gray-700 text-sm">{item.name}</div>
                  </div>
                  <div className="font-bold">₹{item.price}</div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Cart-Interceptor (The MVP Feature) */}
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-1 shadow-sm border border-indigo-100 relative overflow-hidden">
             {/* Decorative shine */}
            <div className="absolute top-0 left-[-100%] w-[50%] h-full bg-gradient-to-r from-transparent via-white/50 to-transparent skew-x-[-20deg] animate-[shine_3s_infinite]" />
            
            <div className="bg-white/60 backdrop-blur-sm p-4 rounded-lg relative z-10">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">✨</span>
                <h3 className="font-bold text-indigo-900 text-sm">Forgot something?</h3>
              </div>

              {loading ? (
                // Loading Skeleton for AI
                <div className="space-y-3 animate-pulse">
                  <div className="h-4 bg-indigo-200/50 rounded w-3/4"></div>
                  <div className="h-4 bg-indigo-200/50 rounded w-1/2"></div>
                  <div className="flex justify-between items-center mt-4 border border-indigo-100 p-2 rounded-lg">
                    <div className="w-10 h-10 bg-indigo-100 rounded-md"></div>
                    <div className="h-8 bg-indigo-200/50 rounded w-20"></div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 animate-[fadeIn_0.3s_ease-out]">
                  <p className="text-indigo-800 text-sm leading-relaxed min-h-[40px]">
                    {recommendationText}
                  </p>
                  
                  {recommendedItem && (
                    <div className="flex justify-between items-center bg-white p-3 rounded-lg border border-indigo-100 shadow-sm transition-transform hover:scale-[1.02]">
                      <div className="flex items-center gap-3">
                         <div className="text-3xl">{recommendedItem.emoji}</div>
                         <div>
                            <div className="font-bold text-xs text-gray-800 leading-tight">{recommendedItem.name}</div>
                            <div className="text-sm font-bold text-indigo-600">₹{recommendedItem.price}</div>
                         </div>
                      </div>
                      <button className="bg-indigo-600 text-white text-xs font-bold px-4 py-2 rounded-md shadow-sm hover:bg-indigo-700 active:bg-indigo-800">
                        ADD
                      </button>
                    </div>
                  )}
                  {error && <div className="text-xs text-gray-400 text-right mt-1">Degraded Mode (Offline)</div>}
                </div>
              )}
            </div>
          </div>
          
          {/* Bill Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mt-6">
            <h2 className="font-bold text-gray-800 mb-3 text-sm">Bill Details</h2>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex justify-between"><span>Item Total</span><span>₹{cartTotal}</span></div>
              <div className="flex justify-between"><span>Delivery Fee</span><span>₹25</span></div>
              <div className="flex justify-between"><span>Handling Fee</span><span>₹4</span></div>
              <div className="flex justify-between font-bold text-black border-t pt-2 mt-2 text-base">
                <span>Grand Total</span>
                <span>₹{cartTotal + 29}</span>
              </div>
            </div>
          </div>

        </div>

        {/* Footer Action */}
        <div className="absolute bottom-0 w-full bg-white border-t p-4 pb-6 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
          <button className="w-full bg-green-600 text-white font-bold py-3 rounded-xl shadow-lg hover:bg-green-700 active:scale-95 transition-all text-lg flex items-center justify-center gap-2">
             Pay ₹{cartTotal + 29}
          </button>
        </div>
      </div>
      
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes shine {
          0% { left: -100%; }
          100% { left: 200%; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(5px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}} />
    </main>
  );
}
