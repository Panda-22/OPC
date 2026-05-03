(() => {
  const fileInput = document.getElementById('fileInput')
  const uploadArea = document.getElementById('uploadArea')
  const uploadStatus = document.getElementById('uploadStatus')
  const analysisPanel = document.getElementById('analysisPanel')
  const chatPanel = document.getElementById('chatPanel')
  const cardsContainer = document.getElementById('cards')
  const chatArea = document.getElementById('chatArea')
  const chatInput = document.getElementById('chatInput')
  const sendBtn = document.getElementById('sendBtn')

  let sessionId = null

  // drag & drop support
  ;['dragover','dragleave','drop'].forEach(ev => {
    document.addEventListener(ev, (e) => {
      e.preventDefault()
      e.stopPropagation()
    })
  })
  uploadArea.addEventListener('dragover', (e) => { uploadArea.style.background = '#fff6e6' })
  uploadArea.addEventListener('dragleave', (e) => { uploadArea.style.background = '' })
  uploadArea.addEventListener('drop', (e) => {
    const dt = e.dataTransfer
    const files = dt.files
    if (files.length > 0) {
      handleFile(files[0])
    }
    uploadArea.style.background = ''
  })

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0])
    }
  })

  function handleFile(file) {
    const form = new FormData()
    form.append('file', file)
    fetch('/upload_report', { method: 'POST', body: form })
      .then(res => res.json())
      .then(data => {
        sessionId = data.session_id
        renderAnalysis(data.analysis)
        uploadStatus.textContent = '上传成功，开始对话。'
        analysisPanel.style.display = 'block'
        chatPanel.style.display = 'block'
      }).catch(err => {
        uploadStatus.textContent = '上传失败，请重试。'
      })
  }

  function renderAnalysis(analysis) {
    cardsContainer.innerHTML = ''
    // Core conclusion card
    const coreCard = document.createElement('div')
    coreCard.className = 'card'
    coreCard.innerHTML = `<h3>核心结论</h3><div>${analysis.core_conclusion || ''}</div>`
    // Radar chart card (simple canvas)
    const radarCard = document.createElement('div')
    radarCard.className = 'card'
    radarCard.innerHTML = `<h3>维度雷达图</h3><canvas class="chart" id="radarChart"></canvas>`
    // Dimension scores card
    const scoreCard = document.createElement('div')
    scoreCard.className = 'card'
    let scoresHtml = '<h3>维度得分对比</h3>'
    if (analysis.dimension_scores && analysis.dimension_scores.length) {
      analysis.dimension_scores.forEach(d => {
        const w = Math.max(4, Math.min(100, d.score))
        scoresHtml += `<div>${d.dimension}: ${d.score} / ?<div style="height:10px;background:#eee;border-radius:6px;overflow:hidden"><div style="width:${w}%;height:100%;background:#f6a623"></div></div></div>`
      })
    } else {
      scoresHtml += '<p>无数据</p>'
    }
    scoreCard.innerHTML = scoresHtml

    cardsContainer.appendChild(coreCard)
    cardsContainer.appendChild(radarCard)
    cardsContainer.appendChild(scoreCard)

    // Radar drawing
    drawRadar('#radarChart', analysis.radars || analysis.radar_points || [])
  }

  function drawRadar(sel, points) {
    // Points is an array of {label, value}
    const canvas = document.querySelector(sel)
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const w = canvas.width = canvas.offsetWidth
    const h = canvas.height = 220
    ctx.clearRect(0,0,w,h)
    const centerX = w/2, centerY = h/2
    const maxR = Math.min(w,h)/2 - 20
    // determine number of axes
    const n = Math.max(5, (points && points.length) || 5)
    // draw grid
    ctx.strokeStyle = '#ddd'
    for (let r = 20; r <= maxR; r += maxR/4) {
      ctx.beginPath()
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2
        const x = centerX + Math.cos(a) * r
        const y = centerY + Math.sin(a) * r
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.closePath()
      ctx.stroke()
    }
    // draw axes
    ctx.strokeStyle = '#bbb'
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2
      const x = centerX + Math.cos(a) * maxR
      const y = centerY + Math.sin(a) * maxR
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.lineTo(x, y)
      ctx.stroke()
      // label
      ctx.fillStyle = '#666'
      ctx.font = '12px sans-serif'
      const lx = centerX + Math.cos(a) * (maxR + 6)
      const ly = centerY + Math.sin(a) * (maxR + 6)
      ctx.fillText(points[i]?.label ?? `L${i+1}`, lx, ly)
    }
    // plot values
    if (points && points.length) {
      ctx.beginPath()
      points.forEach((p, idx) => {
        const a = (idx / points.length) * Math.PI * 2
        const r = (p.value / 10) * maxR
        const x = centerX + Math.cos(a) * r
        const y = centerY + Math.sin(a) * r
        if (idx === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.closePath()
      ctx.fillStyle = 'rgba(255,150,0,.2)'
      ctx.fill()
      ctx.strokeStyle = '#f48a1f'
      ctx.stroke()
    }
  }

  // Chat interactions
  sendBtn.addEventListener('click', sendMessage)
  chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage() })
  function appendMessage(text, side='user') {
    const msg = document.createElement('div')
    msg.className = 'message ' + (side === 'user' ? 'user' : 'assistant')
    msg.textContent = text
    chatArea.appendChild(msg)
    chatArea.scrollTop = chatArea.scrollHeight
  }
  function sendMessage() {
    const text = chatInput.value.trim()
    if (!text || !sessionId) return
    appendMessage(text, 'user')
    chatInput.value = ''
    fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: text })
    })
      .then(res => res.json())
      .then(data => {
        appendMessage(data.reply, 'assistant')
      })
  }
})();
