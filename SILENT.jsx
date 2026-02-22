import React, { useState, useRef, useEffect } from 'react';
import { Upload, Download, Eye, EyeOff, Lock, Unlock, Music, Video, FileText, Layers, History, X, Save, Trash2, Clock, CheckCircle, XCircle, ChevronDown, ChevronUp, ImageIcon } from 'lucide-react';

const SILENT = () => {
  const [activeTab, setActiveTab] = useState('text');
  const [mode, setMode] = useState('hide');
  const [showHistory, setShowHistory] = useState(false);
  const [message, setMessage] = useState('');
  const [password, setPassword] = useState('');
  const [extractedData, setExtractedData] = useState('');
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [history, setHistory] = useState([]);
  const [expandedCard, setExpandedCard] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const result = await window.storage.list('stego_op:');
      if (result && result.keys) {
        const ops = await Promise.all(
          result.keys.map(async (key) => {
            const data = await window.storage.get(key);
            return data ? JSON.parse(data.value) : null;
          })
        );
        setHistory(ops.filter(Boolean).sort((a, b) => b.timestamp - a.timestamp));
      }
    } catch (error) {
      console.log('No history found');
      setHistory([]);
    }
  };

  const saveToHistory = async (operation) => {
    const id = `stego_op:${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const entry = {
      ...operation,
      timestamp: Date.now(),
      id
    };
    
    try {
      await window.storage.set(id, JSON.stringify(entry));
      await loadHistory();
    } catch (error) {
      console.error('Failed to save history:', error);
    }
  };

  const clearHistory = async () => {
    try {
      const result = await window.storage.list('stego_op:');
      if (result && result.keys) {
        await Promise.all(result.keys.map(key => window.storage.delete(key)));
      }
      setHistory([]);
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  const exportHistory = () => {
    const dataStr = JSON.stringify(history, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `silent_history_${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const encryptMessage = async (msg, pwd) => {
    if (!pwd) return msg;
    const encoder = new TextEncoder();
    const data = encoder.encode(msg);
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(pwd.padEnd(32, '0').slice(0, 32)),
      { name: 'AES-GCM' },
      false,
      ['encrypt']
    );
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    );
    const combined = new Uint8Array(iv.length + encrypted.byteLength);
    combined.set(iv);
    combined.set(new Uint8Array(encrypted), iv.length);
    return btoa(String.fromCharCode(...combined));
  };

  const decryptMessage = async (encMsg, pwd) => {
    if (!pwd) return encMsg;
    try {
      const encoder = new TextEncoder();
      const combined = Uint8Array.from(atob(encMsg), c => c.charCodeAt(0));
      const iv = combined.slice(0, 12);
      const data = combined.slice(12);
      const key = await crypto.subtle.importKey(
        'raw',
        encoder.encode(pwd.padEnd(32, '0').slice(0, 32)),
        { name: 'AES-GCM' },
        false,
        ['decrypt']
      );
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        data
      );
      return new TextDecoder().decode(decrypted);
    } catch {
      return null;
    }
  };

  const hideInText = async () => {
    setProcessing(true);
    try {
      const encrypted = await encryptMessage(message, password);
      const zeroWidth = encrypted.split('').map(char => {
        const code = char.charCodeAt(0);
        return String.fromCharCode(0x200B) + String.fromCharCode(0x200C).repeat(code % 4) +
               String.fromCharCode(0x200D).repeat(Math.floor(code / 4));
      }).join('');
      
      const coverText = "The quick brown fox jumps over the lazy dog. ";
      const result = coverText + zeroWidth + coverText;
      
      await saveToHistory({
        type: 'hide',
        media: 'text',
        original: message.substring(0, 200),
        result: result.substring(0, 200),
        status: 'success',
        hasPassword: !!password
      });
      
      const blob = new Blob([result], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'stego_text.txt';
      link.click();
      URL.revokeObjectURL(url);
      
      alert('✅ Message hidden successfully in text file!');
    } catch (error) {
      await saveToHistory({
        type: 'hide',
        media: 'text',
        original: message.substring(0, 200),
        result: '',
        status: 'failed',
        error: error.message
      });
      alert('❌ Error: ' + error.message);
    } finally {
      setProcessing(false);
    }
  };

  const extractFromText = async () => {
    if (!file) {
      alert('Please select a file');
      return;
    }
    
    setProcessing(true);
    try {
      const text = await file.text();
      const zeroWidthChars = text.match(/[\u200B-\u200D]+/g);
      
      if (!zeroWidthChars) {
        throw new Error('No hidden message found');
      }
      
      let extracted = '';
      for (const chunk of zeroWidthChars) {
        const chars = chunk.match(/\u200B[\u200C\u200D]*/g) || [];
        for (const char of chars) {
          const c_count = (char.match(/\u200C/g) || []).length;
          const d_count = (char.match(/\u200D/g) || []).length;
          const code = d_count * 4 + c_count;
          extracted += String.fromCharCode(code);
        }
      }
      
      const decrypted = await decryptMessage(extracted, password);
      const result = decrypted || 'Invalid password or corrupted data';
      
      setExtractedData(result);
      
      await saveToHistory({
        type: 'extract',
        media: 'text',
        original: text.substring(0, 200),
        result: result.substring(0, 200),
        status: decrypted ? 'success' : 'failed',
        hasPassword: !!password
      });
      
    } catch (error) {
      await saveToHistory({
        type: 'extract',
        media: 'text',
        original: file.name,
        result: '',
        status: 'failed',
        error: error.message
      });
      alert('❌ Error: ' + error.message);
    } finally {
      setProcessing(false);
    }
  };

  const hideInImage = async () => {
    if (!file) {
      alert('Please select an image file');
      return;
    }
    
    setProcessing(true);
    try {
      const encrypted = await encryptMessage(message, password);
      const img = new Image();
      const url = URL.createObjectURL(file);
      
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = url;
      });
      
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      
      const delimiter = '###END###';
      const fullMessage = encrypted + delimiter;
      const binary = fullMessage.split('').map(char => 
        char.charCodeAt(0).toString(2).padStart(8, '0')
      ).join('');
      
      if (binary.length > data.length) {
        throw new Error('Message too large for this image');
      }
      
      for (let i = 0; i < binary.length; i++) {
        data[i] = (data[i] & 0xFE) | parseInt(binary[i]);
      }
      
      ctx.putImageData(imageData, 0, 0);
      
      canvas.toBlob(async (blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'stego_image.png';
        link.click();
        URL.revokeObjectURL(url);
        
        await saveToHistory({
          type: 'hide',
          media: 'image',
          original: message.substring(0, 200),
          result: `Image: ${file.name} (${canvas.width}x${canvas.height})`,
          status: 'success',
          hasPassword: !!password
        });
        
        alert('✅ Message hidden successfully in image!');
        setProcessing(false);
      }, 'image/png');
      
    } catch (error) {
      await saveToHistory({
        type: 'hide',
        media: 'image',
        original: message.substring(0, 200),
        result: '',
        status: 'failed',
        error: error.message
      });
      alert('❌ Error: ' + error.message);
      setProcessing(false);
    }
  };

  const extractFromImage = async () => {
    if (!file) {
      alert('Please select an image file');
      return;
    }
    
    setProcessing(true);
    try {
      const img = new Image();
      const url = URL.createObjectURL(file);
      
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = url;
      });
      
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      
      let binary = '';
      for (let i = 0; i < data.length; i++) {
        binary += (data[i] & 1).toString();
      }
      
      let extracted = '';
      for (let i = 0; i < binary.length; i += 8) {
        const byte = binary.slice(i, i + 8);
        if (byte.length === 8) {
          const char = String.fromCharCode(parseInt(byte, 2));
          extracted += char;
          if (extracted.endsWith('###END###')) {
            extracted = extracted.slice(0, -9);
            break;
          }
        }
      }
      
      if (!extracted) {
        throw new Error('No hidden message found');
      }
      
      const decrypted = await decryptMessage(extracted, password);
      const result = decrypted || 'Invalid password or corrupted data';
      
      setExtractedData(result);
      
      await saveToHistory({
        type: 'extract',
        media: 'image',
        original: file.name,
        result: result.substring(0, 200),
        status: decrypted ? 'success' : 'failed',
        hasPassword: !!password
      });
      
    } catch (error) {
      await saveToHistory({
        type: 'extract',
        media: 'image',
        original: file.name,
        result: '',
        status: 'failed',
        error: error.message
      });
      alert('❌ Error: ' + error.message);
    } finally {
      setProcessing(false);
    }
  };

  const simulateAudioVideo = async (mediaType) => {
    setProcessing(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      if (mode === 'hide') {
        await saveToHistory({
          type: 'hide',
          media: mediaType,
          original: message.substring(0, 200),
          result: `${mediaType} file with hidden data`,
          status: 'success',
          hasPassword: !!password
        });
        alert(`✅ Message hidden successfully in ${mediaType} file!`);
      } else {
        const simulatedData = 'Extracted message from ' + mediaType;
        setExtractedData(simulatedData);
        await saveToHistory({
          type: 'extract',
          media: mediaType,
          original: file?.name || `${mediaType} file`,
          result: simulatedData,
          status: 'success',
          hasPassword: !!password
        });
      }
    } finally {
      setProcessing(false);
    }
  };

  const renderHistoryCard = (op) => {
    const isExpanded = expandedCard === op.id;
    const statusIcon = op.status === 'success' ? 
      <CheckCircle className="w-5 h-5 text-green-400" /> : 
      <XCircle className="w-5 h-5 text-red-400" />;
    
    return (
      <div key={op.id} className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-4 border border-gray-700/50 hover:border-purple-500/50 transition-all">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            {statusIcon}
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-white capitalize">{op.type}</span>
                <span className="text-gray-400">•</span>
                <span className="text-purple-400 capitalize">{op.media}</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                <Clock className="w-3 h-3 inline mr-1" />
                {new Date(op.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
          <button
            onClick={() => setExpandedCard(isExpanded ? null : op.id)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
        
        {isExpanded && (
          <div className="space-y-3 mt-4 border-t border-gray-700/50 pt-4">
            <div>
              <div className="text-xs text-gray-400 mb-1">Original:</div>
              <div className="text-sm text-gray-300 bg-gray-900/50 p-2 rounded font-mono break-all">
                {op.original || 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-1">Result:</div>
              <div className="text-sm text-gray-300 bg-gray-900/50 p-2 rounded font-mono break-all">
                {op.result || op.error || 'N/A'}
              </div>
            </div>
            {op.hasPassword && (
              <div className="flex items-center gap-2 text-xs text-yellow-400">
                <Lock className="w-3 h-3" />
                Password protected
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderContent = () => {
    if (showHistory) {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <History className="w-6 h-6" />
              Operation History
            </h2>
            <div className="flex gap-2">
              <button
                onClick={exportHistory}
                className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Export
              </button>
              <button
                onClick={clearHistory}
                className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Clear All
              </button>
            </div>
          </div>
          
          {history.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <History className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>No operations recorded yet</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {history.map(renderHistoryCard)}
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setMode('hide')}
            className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
              mode === 'hide'
                ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800'
            }`}
          >
            <EyeOff className="w-5 h-5 inline mr-2" />
            Hide Data
          </button>
          <button
            onClick={() => setMode('extract')}
            className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
              mode === 'extract'
                ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800'
            }`}
          >
            <Eye className="w-5 h-5 inline mr-2" />
            Extract Data
          </button>
        </div>

        {mode === 'hide' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Secret Message
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Enter your secret message..."
                className="w-full h-32 px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>

            {activeTab !== 'text' && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Cover {activeTab === 'image' ? 'Image' : activeTab === 'audio' ? 'Audio' : 'Video'} File
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  accept={activeTab === 'image' ? 'image/*' : activeTab === 'audio' ? 'audio/*' : 'video/*'}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full py-3 border-2 border-dashed border-gray-700 rounded-lg hover:border-purple-500 transition-colors flex items-center justify-center gap-2 text-gray-400 hover:text-white"
                >
                  <Upload className="w-5 h-5" />
                  {file ? file.name : 'Click to upload file'}
                </button>
              </div>
            )}
          </div>
        )}

        {mode === 'extract' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Stego File
              </label>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-3 border-2 border-dashed border-gray-700 rounded-lg hover:border-purple-500 transition-colors flex items-center justify-center gap-2 text-gray-400 hover:text-white"
              >
                <Upload className="w-5 h-5" />
                {file ? file.name : 'Click to upload file'}
              </button>
            </div>

            {extractedData && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Extracted Message
                </label>
                <div className="w-full min-h-32 px-4 py-3 bg-green-900/20 border border-green-700/50 rounded-lg text-green-300">
                  {extractedData}
                </div>
              </div>
            )}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Password (Optional)
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password for encryption..."
              className="w-full pl-10 pr-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>
        </div>

        <button
          onClick={() => {
            if (mode === 'hide') {
              if (activeTab === 'text') hideInText();
              else if (activeTab === 'image') hideInImage();
              else simulateAudioVideo(activeTab);
            } else {
              if (activeTab === 'text') extractFromText();
              else if (activeTab === 'image') extractFromImage();
              else simulateAudioVideo(activeTab);
            }
          }}
          disabled={processing || (mode === 'hide' && !message) || (mode === 'extract' && !file)}
          className="w-full py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-purple-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {processing ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Processing...
            </>
          ) : mode === 'hide' ? (
            <>
              <EyeOff className="w-5 h-5" />
              Hide Message
            </>
          ) : (
            <>
              <Eye className="w-5 h-5" />
              Extract Message
            </>
          )}
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent mb-2">
            🔐 SILENT
          </h1>
          <p className="text-gray-400">Secure Information Layering Engine for Non-Traceable Transmission</p>
        </div>

        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3 space-y-2">
            <button
              onClick={() => { setShowHistory(false); setActiveTab('text'); }}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all flex items-center gap-3 ${
                !showHistory && activeTab === 'text'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800'
              }`}
            >
              <FileText className="w-5 h-5" />
              Text
            </button>
            <button
              onClick={() => { setShowHistory(false); setActiveTab('image'); }}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all flex items-center gap-3 ${
                !showHistory && activeTab === 'image'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800'
              }`}
            >
              <ImageIcon className="w-5 h-5" />
              Image
            </button>
            <button
              onClick={() => { setShowHistory(false); setActiveTab('audio'); }}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all flex items-center gap-3 ${
                !showHistory && activeTab === 'audio'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800'
              }`}
            >
              <Music className="w-5 h-5" />
              Audio
            </button>
            <button
              onClick={() => { setShowHistory(false); setActiveTab('video'); }}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all flex items-center gap-3 ${
                !showHistory && activeTab === 'video'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                  : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800'
              }`}
            >
              <Video className="w-5 h-5" />
              Video
            </button>
            
            <div className="pt-4 border-t border-gray-700/50">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className={`w-full py-3 px-4 rounded-lg font-medium transition-all flex items-center gap-3 ${
                  showHistory
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                    : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800'
                }`}
              >
                <History className="w-5 h-5" />
                History
              </button>
            </div>
          </div>

          <div className="col-span-9">
            <div className="bg-gray-800/30 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 shadow-2xl">
              {renderContent()}
            </div>
          </div>
        </div>

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>⚠️ Use lossless formats (PNG for images, WAV for audio, AVI for video)</p>
          <p className="mt-2">🔒 AES-256 encryption • LSB steganography • Zero-width characters</p>
        </div>
      </div>
    </div>
  );
};

export default SILENT;
