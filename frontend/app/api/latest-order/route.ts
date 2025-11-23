import { NextResponse } from 'next/server';
import { readdir, readFile } from 'fs/promises';
import { join } from 'path';

export async function GET() {
  try {
    const ordersDir = join(process.cwd(), '..', 'backend', 'orders');
    
    // Get all order files
    const files = await readdir(ordersDir);
    const orderFiles = files.filter(f => f.startsWith('order_') && f.endsWith('.json'));
    
    if (orderFiles.length === 0) {
      return NextResponse.json({ error: 'No orders found' }, { status: 404 });
    }
    
    // Sort by filename (timestamp) and get the latest
    orderFiles.sort();
    const latestFile = orderFiles[orderFiles.length - 1];
    
    // Read the latest order
    const filePath = join(ordersDir, latestFile);
    const content = await readFile(filePath, 'utf-8');
    const orderData = JSON.parse(content);
    
    return NextResponse.json(orderData);
  } catch (error) {
    console.error('Error fetching latest order:', error);
    return NextResponse.json({ error: 'Failed to fetch order' }, { status: 500 });
  }
}
