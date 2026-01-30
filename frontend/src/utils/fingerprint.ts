/**
 * Fingerprinting Utilities
 * Privacy-preserving fingerprint generation
 */

/**
 * Simple hash function for strings (privacy-preserving)
 */
export function hashString(str: string): string {
  if (!str) return '';
  
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  // Convert to hex string
  return Math.abs(hash).toString(16).padStart(8, '0');
}

/**
 * Generate canvas fingerprint (hashed for privacy)
 */
export async function generateCanvasFingerprint(): Promise<string> {
  try {
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 50;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    // Draw various elements to create unique fingerprint
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    
    ctx.fillStyle = '#069';
    ctx.fillText('PassiveGuard 🔒', 2, 15);
    
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Bot Detection', 4, 35);
    
    // Add some geometric shapes
    ctx.beginPath();
    ctx.arc(50, 25, 10, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.strokeStyle = '#f00';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(150, 10);
    ctx.lineTo(180, 40);
    ctx.stroke();

    // Get data URL and hash it
    const dataUrl = canvas.toDataURL();
    return hashString(dataUrl);
  } catch (e) {
    return '';
  }
}

/**
 * Generate audio fingerprint (hashed for privacy)
 */
export async function generateAudioFingerprint(): Promise<string> {
  try {
    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContext) return '';

    const context = new AudioContext();
    const oscillator = context.createOscillator();
    const analyser = context.createAnalyser();
    const gainNode = context.createGain();
    const scriptProcessor = context.createScriptProcessor(4096, 1, 1);

    // Configure nodes
    gainNode.gain.value = 0; // Mute
    oscillator.type = 'triangle';
    oscillator.frequency.value = 10000;

    // Connect nodes
    oscillator.connect(analyser);
    analyser.connect(scriptProcessor);
    scriptProcessor.connect(gainNode);
    gainNode.connect(context.destination);

    return new Promise((resolve) => {
      const fingerprint: number[] = [];
      
      scriptProcessor.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0);
        
        // Sample some values
        for (let i = 0; i < Math.min(inputData.length, 100); i += 10) {
          fingerprint.push(inputData[i]);
        }

        if (fingerprint.length >= 100) {
          oscillator.stop();
          context.close();
          
          // Hash the fingerprint values
          const hash = hashString(fingerprint.map(v => v.toFixed(6)).join(','));
          resolve(hash);
        }
      };

      oscillator.start(0);
      
      // Timeout fallback
      setTimeout(() => {
        try {
          oscillator.stop();
          context.close();
        } catch (e) {}
        resolve(hashString(fingerprint.map(v => v.toFixed(6)).join(',')));
      }, 500);
    });
  } catch (e) {
    return '';
  }
}

/**
 * Generate combined fingerprint hash
 */
export function generateCombinedHash(...values: string[]): string {
  return hashString(values.filter(Boolean).join('|'));
}
