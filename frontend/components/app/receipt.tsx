'use client';

import { motion } from 'motion/react';

interface OrderItem {
  drinkType: string;
  size: string;
  milk: string | null;
  extras: string[];
  name: string;
}

interface ReceiptData {
  customer_name: string;
  orders: OrderItem[];
  grand_total: number;
  timestamp: string;
}

interface ReceiptProps {
  data: ReceiptData;
  onClose: () => void;
}

export function Receipt({ data, onClose }: ReceiptProps) {
  const date = new Date(data.timestamp);
  
  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 bottom-0 w-[400px] p-8 overflow-y-auto"
      style={{ 
        background: 'linear-gradient(135deg, #FFFEF7 0%, #FFF8E7 100%)',
        borderLeft: '4px solid #6F4E37',
        boxShadow: '-8px 0 24px rgba(0, 0, 0, 0.2)',
        zIndex: 9999,
      }}
    >
        {/* Header */}
        <div className="text-center mb-6 pb-4 border-b-2 border-dashed" style={{ borderColor: '#8B6F47' }}>
          <h2 className="text-3xl font-bold mb-2" style={{ color: '#6F4E37' }}>
            MoonBucks
          </h2>
          <p className="text-xs uppercase tracking-widest" style={{ color: '#8B7355' }}>
            Coffee & Voice AI
          </p>
          <p className="text-xs mt-2" style={{ color: '#8B7355' }}>
            {date.toLocaleDateString()} • {date.toLocaleTimeString()}
          </p>
        </div>

        {/* Customer Name */}
        <div className="mb-6">
          <p className="text-sm uppercase tracking-wide" style={{ color: '#8B7355' }}>Order For</p>
          <p className="text-2xl font-bold" style={{ color: '#6F4E37' }}>{data.customer_name}</p>
        </div>

        {/* Orders */}
        <div className="space-y-4 mb-6">
          {data.orders.map((order, index) => (
            <div key={index} className="pb-4 border-b" style={{ borderColor: '#E8DCC4' }}>
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <p className="font-semibold text-lg" style={{ color: '#6F4E37' }}>
                    {order.drinkType}
                  </p>
                  <p className="text-sm" style={{ color: '#8B7355' }}>
                    Size: <span className="capitalize">{order.size}</span>
                  </p>
                  {order.milk && (
                    <p className="text-sm" style={{ color: '#8B7355' }}>
                      Milk: <span className="capitalize">{order.milk}</span>
                    </p>
                  )}
                  {order.extras && order.extras.length > 0 && (
                    <p className="text-sm" style={{ color: '#8B7355' }}>
                      Extras: <span className="capitalize">{order.extras.join(', ')}</span>
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Total */}
        <div className="pt-4 border-t-2 border-dashed mb-6" style={{ borderColor: '#8B6F47' }}>
          <div className="flex justify-between items-center">
            <span className="text-xl font-bold" style={{ color: '#6F4E37' }}>Grand Total</span>
            <span className="text-2xl font-bold" style={{ color: '#6F4E37' }}>
              ${data.grand_total.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center pt-4 border-t" style={{ borderColor: '#E8DCC4' }}>
          <p className="text-sm mb-2" style={{ color: '#8B7355' }}>
            Please wait for your name to be called
          </p>
          <p className="text-xs" style={{ color: '#8B7355' }}>
            Thank you for choosing MoonBucks!
          </p>
          <p className="text-xs mt-3 italic" style={{ color: '#B8956A' }}>
            Powered by Murf Falcon TTS
          </p>
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="mt-6 w-full py-3 rounded-lg font-semibold text-white transition-all hover:scale-105"
          style={{ 
            background: 'linear-gradient(135deg, #6F4E37 0%, #5D4037 100%)'
          }}
        >
          Close Receipt
        </button>
    </motion.div>
  );
}
