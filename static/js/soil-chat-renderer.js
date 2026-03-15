(function () {
    'use strict';

    const SOIL_PREFIX = '__SOIL_CHAT_PAYLOAD__:';

    function escapeHtml(value) {
        if (value === null || value === undefined) {
            return '';
        }
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function formatNumber(value, suffix) {
        const num = Number(value);
        if (!Number.isFinite(num)) {
            return 'N/A';
        }
        return `${num.toFixed(2)}${suffix || ''}`;
    }

    function parseSoilPayload(raw) {
        if (!raw || typeof raw !== 'string' || !raw.startsWith(SOIL_PREFIX)) {
            return null;
        }

        try {
            return JSON.parse(raw.slice(SOIL_PREFIX.length));
        } catch (error) {
            console.error('Failed to parse soil payload:', error);
            return null;
        }
    }

    function renderUploadPayload(payload) {
        const title = escapeHtml(payload.title || 'Soil Report Analysis');
        const reportUrl = payload.report_url ? escapeHtml(payload.report_url) : null;
        const fileName = escapeHtml(payload.file_name || 'Soil report');
        const previewUrl = payload.preview_url ? escapeHtml(payload.preview_url) : null;

        let mediaBlock = '';
        if (previewUrl) {
            mediaBlock = `<img class="soil-report-preview" src="${previewUrl}" alt="Uploaded soil report preview">`;
        }

        const linkText = 'Click: To view uploaded report';
        const linkBlock = reportUrl
            ? `<a class="soil-link" href="${reportUrl}" target="_blank" rel="noopener noreferrer">${linkText}</a>`
            : `<span>${fileName}</span>`;

        return `
            <div class="soil-card">
                <h4>${title}</h4>
                ${mediaBlock}
                <div>${linkBlock}</div>
            </div>
        `;
    }

    function renderAnalysisPayload(payload) {
        const p = payload.soil_params || {};
        const crops = Array.isArray(payload.recommended_crops) ? payload.recommended_crops : [];
        const primaryCrop = crops.length > 0 ? crops[0] : null;
        const secondaryCrops = crops.length > 1 ? crops.slice(1) : [];
        const secondaryText = secondaryCrops.length > 0 ? secondaryCrops.map(escapeHtml).join(', ') : 'No additional crops';

        const fertilizerUrl = payload.fertilizer_report_url ? escapeHtml(payload.fertilizer_report_url) : null;
        const fertilizerLink = fertilizerUrl
            ? `<a class="soil-link" href="${fertilizerUrl}" target="_blank" rel="noopener noreferrer">Click: To view Fertilizer Report</a>`
            : '<span>Fertilizer report is not available.</span>';

        return `
            <div class="soil-card">
                <h4>${escapeHtml(payload.title || 'Soil Report Analysis')}</h4>
                <div><strong>District:</strong> ${escapeHtml(payload.district || 'N/A')}</div>
                <div><strong>State:</strong> ${escapeHtml(payload.state || 'N/A')}</div>
                <div><strong>Soil Type:</strong> ${escapeHtml(payload.soil_type || 'N/A')}</div>

                <div style="margin-top:10px;"><strong>Soil Parameters</strong></div>
                <div class="soil-params-grid">
                    <div class="soil-param-item">pH: ${formatNumber(p.ph, '')}</div>
                    <div class="soil-param-item">EC: ${formatNumber(p.ec, '')}</div>
                    <div class="soil-param-item">Organic Carbon: ${formatNumber(p.organic_carbon, '%')}</div>
                    <div class="soil-param-item">Nitrogen: ${formatNumber(p.nitrogen, ' kg/ha')}</div>
                    <div class="soil-param-item">Phosphorus: ${formatNumber(p.phosphorus, ' kg/ha')}</div>
                    <div class="soil-param-item">Potassium: ${formatNumber(p.potassium, ' kg/ha')}</div>
                    <div class="soil-param-item">Zinc: ${formatNumber(p.zinc, ' ppm')}</div>
                    <div class="soil-param-item">Copper: ${formatNumber(p.copper, ' ppm')}</div>
                    <div class="soil-param-item">Iron: ${formatNumber(p.iron, ' ppm')}</div>
                    <div class="soil-param-item">Manganese: ${formatNumber(p.manganese, ' ppm')}</div>
                    <div class="soil-param-item">Sulphur: ${formatNumber(p.sulphur, ' ppm')}</div>
                </div>

                <div class="soil-recommendation-panel">
                    <div><strong>Main Recommendation</strong></div>
                    <div class="predicted-crop-pill">${primaryCrop ? `Predicted Crop: ${escapeHtml(primaryCrop)}` : 'Predicted Crop: N/A'}</div>
                    <div class="other-crops"><strong>Other Suitable Crops:</strong> ${secondaryText}</div>
                </div>

                <div class="fertilizer-box">
                    <strong>Fertilizer Recommendation:</strong><br>
                    ${escapeHtml(payload.fertilizer_summary || 'N/A')}
                </div>

                <div style="margin-top:10px;">${fertilizerLink}</div>
            </div>
        `;
    }

    function renderPayloadElement(element) {
        const payload = parseSoilPayload(element.getAttribute('data-payload'));
        if (!payload || !payload.type) {
            return;
        }

        if (payload.type === 'soil_report_upload') {
            element.innerHTML = renderUploadPayload(payload);
            return;
        }

        if (payload.type === 'soil_report_analysis') {
            element.innerHTML = renderAnalysisPayload(payload);
        }
    }

    function renderSoilChatPayloads(root) {
        const scope = root || document;
        const payloadElements = scope.querySelectorAll('.soil-message-payload');
        payloadElements.forEach(renderPayloadElement);
    }

    window.renderSoilChatPayloads = renderSoilChatPayloads;
})();
