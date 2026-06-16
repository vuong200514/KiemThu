const dropArea = document.getElementById('drop-area');
const fileElem = document.getElementById('fileElem');
const fileNameDisplay = document.getElementById('file-name');
const submitBtn = document.getElementById('submit-btn');

const loader = document.getElementById('loader');
const results = document.getElementById('results');
const errorCard = document.getElementById('error-card');
const successCard = document.getElementById('success-card');

const errorMessage = document.getElementById('error-message');
const analyzeMessage = document.getElementById('analyze-message');
const aiCode = document.getElementById('ai-code');
const execOutput = document.getElementById('exec-output');
const reportLink = document.getElementById('report-link');

let currentFiles = [];
let draggedItemIndex = null;

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropArea.classList.add('highlight');
}

function unhighlight(e) {
    dropArea.classList.remove('highlight');
}

dropArea.addEventListener('drop', handleDrop, false);
fileElem.addEventListener('change', handleFiles, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles({ target: { files } });
}

function handleFiles(e) {
    const files = Array.from(e.target.files);
    const newFiles = files.filter(file => file.name.endsWith('.py'));

    // Thêm file mới vào danh sách hiện tại (bỏ qua file đã tồn tại)
    newFiles.forEach(newFile => {
        if (!currentFiles.some(f => f.name === newFile.name)) {
            currentFiles.push(newFile);
        }
    });

    // Xóa value của input để có thể kích hoạt sự kiện change ở những lần chọn sau
    if (e.target.id === 'fileElem') {
        e.target.value = '';
    }

    const hasError = files.length > 0 && newFiles.length === 0;
    renderFileList(hasError);
}

function renderFileList(hasError = false) {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';

    if (currentFiles.length > 0) {
        fileNameDisplay.style.display = 'block';
        fileNameDisplay.innerHTML = `Đã chọn: <strong>${currentFiles.length}</strong> file`;
        submitBtn.disabled = false;

        currentFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'file-item';

            li.draggable = true;
            li.dataset.index = index;
            li.style.cursor = 'grab';

            li.addEventListener('dragstart', function(e) {
                draggedItemIndex = index;
                e.dataTransfer.effectAllowed = 'move';
                this.style.opacity = '0.4';
            });

            li.addEventListener('dragover', function(e) {
                e.preventDefault(); 
                e.dataTransfer.dropEffect = 'move';
                this.style.transform = 'scale(1.02)';
                this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
            });

            li.addEventListener('dragleave', function(e) {
                this.style.transform = '';
                this.style.boxShadow = '';
            });

            li.addEventListener('drop', function(e) {
                e.stopPropagation(); // Ngăn sự kiện lọt ra dropArea
                this.style.transform = '';
                this.style.boxShadow = '';
                
                if (draggedItemIndex !== null && draggedItemIndex !== index) {
                    const draggedFile = currentFiles[draggedItemIndex];
                    currentFiles.splice(draggedItemIndex, 1);
                    currentFiles.splice(index, 0, draggedFile);
                    renderFileList();
                }
                return false;
            });

            li.addEventListener('dragend', function(e) {
                this.style.opacity = '1';
                draggedItemIndex = null;
            });

            const nameSpan = document.createElement('span');
            nameSpan.className = 'file-name-text';
            nameSpan.innerHTML = '&#9776; &nbsp;' + file.name; // Icon kéo thả
            nameSpan.title = file.name;

            const removeSpan = document.createElement('span');
            removeSpan.className = 'remove-file';
            removeSpan.innerHTML = '&#10005;'; // X mark
            removeSpan.title = 'Xóa file này';
            removeSpan.onclick = (event) => {
                event.stopPropagation();
                currentFiles.splice(index, 1);
                renderFileList();
            };

            const controls = document.createElement('div');
            controls.className = 'file-controls';
            controls.style.display = 'flex';
            controls.style.alignItems = 'center';
            controls.appendChild(removeSpan);

            li.appendChild(nameSpan);
            li.appendChild(controls);
            fileList.appendChild(li);
        });
    } else {
        fileNameDisplay.style.display = 'block';
        if (hasError) {
            fileNameDisplay.innerHTML = '❌ <span style="color: var(--error);">Chỉ chấp nhận file Python (.py)</span>';
        } else {
            fileNameDisplay.textContent = 'Hoặc kéo thả file vào đây';
        }
        submitBtn.disabled = true;
    }
}

submitBtn.addEventListener('click', async () => {
    if (currentFiles.length === 0) return;

    // Reset UI
    results.classList.add('hidden');
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.innerHTML = '';
    loader.classList.remove('hidden');
    submitBtn.disabled = true;
    
    // Vô hiệu hóa nút xóa file khi đang chạy
    document.querySelectorAll('.remove-file').forEach(el => el.style.display = 'none');
    
    const allReports = [];

    for (let i = 0; i < currentFiles.length; i++) {
        const file = currentFiles[i];
        document.getElementById('loader-message').textContent = `Đang xử lý ${i + 1}/${currentFiles.length}: ${file.name}...`;

        // Đặt lại hiệu ứng cho mỗi file
        document.querySelectorAll('.step').forEach(s => s.className = 'step pending');
        document.getElementById('step-analyze').className = 'step active';

        let stepIndex = 0;
        const steps = ['step-analyze', 'step-ai', 'step-exec'];

        const stepInterval = setInterval(() => {
            if (stepIndex < steps.length - 1) {
                document.getElementById(steps[stepIndex]).className = 'step done';
                stepIndex++;
                document.getElementById(steps[stepIndex]).className = 'step active';
            }
        }, 1500); // Mỗi 1.5s nhảy 1 bước

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/test-file', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            // Create Result Card
            const card = document.createElement('div');
            card.className = `result-card ${data.status === 'success' ? 'success' : 'error'}`;
            card.style.marginBottom = '20px';

            if (data.status === 'success') {
                allReports.push({
                    file_name: file.name,
                    status: 'success',
                    report_url: data.report_url,
                    message: ''
                });

                const analyzeMessage = data.analyze_result.message || 'Phân tích thành công.';
                const aiCode = data.ai_result.test_code || 'Không có mã sinh ra.';
                const execOutput = data.exec_result.output || 'Không có output.';
                let reportHtml = '';
                if (data.report_url) {
                    reportHtml = `<div class="result-action"><a href="${data.report_url}" target="_blank" class="button secondary">Xem Báo Cáo Chi Tiết</a></div>`;
                }

                card.innerHTML = `
                    <h3 style="margin-top:0; padding-bottom: 10px; border-bottom: 1px solid #eee;">File: ${file.name}</h3>
                    <div class="result-item">
                        <h3>📊 Phân tích</h3>
                        <p>${analyzeMessage}</p>
                    </div>
                    <div class="result-item">
                        <h3>AI Test Code</h3>
                        <pre><code>${aiCode.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>
                    </div>
                    <div class="result-item">
                        <h3>⚙️ Kết quả chạy</h3>
                        <pre><code>${execOutput.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>
                    </div>
                    ${reportHtml}
                `;
            } else {
                const errorMessage = data.message || 'Có lỗi xảy ra trong quá trình xử lý.';
                allReports.push({
                    file_name: file.name,
                    status: 'error',
                    report_url: null,
                    message: errorMessage
                });
                card.innerHTML = `
                    <h3 style="margin-top:0; padding-bottom: 10px; border-bottom: 1px solid #eee;">File: ${file.name}</h3>
                    <h3>❌ Lỗi</h3>
                    <p>${errorMessage}</p>
                `;
            }
            resultsContainer.appendChild(card);

        } catch (error) {
            allReports.push({
                file_name: file.name,
                status: 'error',
                report_url: null,
                message: error.message
            });
            const card = document.createElement('div');
            card.className = 'result-card error';
            card.style.marginBottom = '20px';
            card.innerHTML = `
                <h3 style="margin-top:0; padding-bottom: 10px; border-bottom: 1px solid #eee;">File: ${file.name}</h3>
                <h3>❌ Lỗi hệ thống</h3>
                <p>Lỗi kết nối máy chủ: ${error.message}</p>
            `;
            resultsContainer.appendChild(card);
        }

        clearInterval(stepInterval);
    }



    document.querySelectorAll('.step').forEach(s => {
        s.className = 'step done';
    });

    document.getElementById('loader-message').textContent = 'Đã hoàn thành tất cả!';
    setTimeout(() => {
        loader.classList.add('hidden');
        results.classList.remove('hidden');
        submitBtn.disabled = false;
        document.getElementById('loader-message').textContent = 'Đang xử lý, vui lòng chờ...';
        
        // Xóa danh sách file sau khi chạy xong
        currentFiles = [];
        renderFileList();
    }, 1000);
});
