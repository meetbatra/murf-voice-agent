import { NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';

export async function GET() {
  try {
    const logPath = join(process.cwd(), '..', 'backend', 'wellness_data', 'wellness_log.json');
    const fileContent = await readFile(logPath, 'utf-8');
    const data = JSON.parse(fileContent);
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error reading wellness log:', error);
    return NextResponse.json(
      { error: 'No wellness log found' },
      { status: 404 }
    );
  }
}
