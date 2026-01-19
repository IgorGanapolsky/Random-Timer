import {createCanvas} from 'canvas';
import fs from 'fs';
import path from 'path';

const ASSETS_DIR = path.join(__dirname, '..', 'assets');

const writeAsset = (filename: string, buffer: Buffer) => {
  fs.mkdirSync(ASSETS_DIR, {recursive: true});
  const targetPath = path.join(ASSETS_DIR, filename);
  fs.writeFileSync(targetPath, buffer);
  return targetPath;
};

const generateAppIcon = () => {
  const canvas = createCanvas(1024, 1024);
  const ctx = canvas.getContext('2d');

  const gradient = ctx.createLinearGradient(0, 0, 1024, 1024);
  gradient.addColorStop(0, '#667eea');
  gradient.addColorStop(1, '#764ba2');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 1024, 1024);

  ctx.beginPath();
  ctx.moveTo(512, 200);
  ctx.quadraticCurveTo(300, 250, 300, 450);
  ctx.quadraticCurveTo(300, 650, 512, 824);
  ctx.quadraticCurveTo(724, 650, 724, 450);
  ctx.quadraticCurveTo(724, 250, 512, 200);
  ctx.closePath();

  ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
  ctx.fill();

  ctx.beginPath();
  ctx.arc(512, 400, 80, 0, Math.PI * 2);
  ctx.strokeStyle = '#667eea';
  ctx.lineWidth = 20;
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(512, 480);
  ctx.lineTo(512, 650);
  ctx.lineTo(490, 650);
  ctx.lineTo(490, 620);
  ctx.lineTo(512, 620);
  ctx.lineTo(512, 590);
  ctx.lineTo(534, 590);
  ctx.lineTo(534, 620);
  ctx.lineTo(556, 620);
  ctx.lineTo(556, 650);
  ctx.lineTo(534, 650);
  ctx.closePath();
  ctx.fillStyle = '#667eea';
  ctx.fill();

  const iconPath = writeAsset('icon.png', canvas.toBuffer('image/png'));
  console.log('✅ App icon generated at:', iconPath);

  const adaptivePath = writeAsset('adaptive-icon.png', canvas.toBuffer('image/png'));
  console.log('✅ Adaptive icon generated at:', adaptivePath);
};

const generateSplashScreen = () => {
  const canvas = createCanvas(1242, 2436);
  const ctx = canvas.getContext('2d');

  const gradient = ctx.createLinearGradient(0, 0, 1242, 2436);
  gradient.addColorStop(0, '#667eea');
  gradient.addColorStop(1, '#764ba2');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 1242, 2436);

  const scale = 0.5;
  const offsetX = (1242 - 1024 * scale) / 2;
  const offsetY = (2436 - 1024 * scale) / 2 - 200;

  ctx.save();
  ctx.translate(offsetX, offsetY);
  ctx.scale(scale, scale);

  ctx.beginPath();
  ctx.moveTo(512, 200);
  ctx.quadraticCurveTo(300, 250, 300, 450);
  ctx.quadraticCurveTo(300, 650, 512, 824);
  ctx.quadraticCurveTo(724, 650, 724, 450);
  ctx.quadraticCurveTo(724, 250, 512, 200);
  ctx.closePath();

  ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
  ctx.fill();

  ctx.beginPath();
  ctx.arc(512, 400, 80, 0, Math.PI * 2);
  ctx.strokeStyle = '#667eea';
  ctx.lineWidth = 20;
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(512, 480);
  ctx.lineTo(512, 650);
  ctx.lineTo(490, 650);
  ctx.lineTo(490, 620);
  ctx.lineTo(512, 620);
  ctx.lineTo(512, 590);
  ctx.lineTo(534, 590);
  ctx.lineTo(534, 620);
  ctx.lineTo(556, 620);
  ctx.lineTo(556, 650);
  ctx.lineTo(534, 650);
  ctx.closePath();
  ctx.fillStyle = '#667eea';
  ctx.fill();

  ctx.restore();

  ctx.fillStyle = 'white';
  ctx.font = 'bold 120px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';
  ctx.textAlign = 'center';
  ctx.fillText('Random Timer', 621, 1600);

  ctx.font = '60px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto';
  ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
  ctx.fillText('Chaotic intervals', 621, 1700);

  const splashPath = writeAsset('splash.png', canvas.toBuffer('image/png'));
  console.log('✅ Splash screen generated at:', splashPath);
};

try {
  generateAppIcon();
  generateSplashScreen();
} catch (error) {
  console.log('⚠️  Please install canvas package first:');
  console.log('npm install canvas');
  console.log('\nNote: You may need to install system dependencies:');
  console.log('macOS: brew install pkg-config cairo pango libpng jpeg giflib librsvg');
}
