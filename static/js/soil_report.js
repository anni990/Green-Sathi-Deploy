document.addEventListener('DOMContentLoaded', function() {
    // Language translations - Define this first to avoid reference errors
    const translations = {
        english: {
            pageTitle: 'Soil Report Analysis',
            pageDescription: 'Upload your soil report to get personalized crop and fertilizer recommendations based on your soil parameters.',
            uploadTitle: 'Upload Soil Report',
            uploadInstructions: 'Please upload your soil test report or take a picture to analyze.',
            uploadTabText: 'Upload Report',
            cameraTabText: 'Take Picture',
            uploadHint: 'Drag and drop your soil report or click to browse',
            captureText: 'Capture',
            switchCameraText: 'Switch Camera',
            retakeText: 'Retake',
            processText: 'Process Soil Report',
            processingText: 'Processing your soil report...',
            pleaseWaitText: 'Please wait, this may take a moment.',
            resultTitle: 'Soil Analysis Results',
            soilParamsTitle: 'Soil Parameters',
            locationInfoTitle: 'Location Information',
            phLabel: 'pH Level',
            ecLabel: 'EC',
            ocLabel: 'Organic Carbon',
            phosphorusLabel: 'Phosphorus',
            potassiumLabel: 'Potassium',
            zincLabel: 'Zinc',
            copperLabel: 'Copper',
            ironLabel: 'Iron',
            manganeseLabel: 'Manganese',
            districtResultLabel: 'District',
            stateResultLabel: 'State',
            recommendedCropsTitle: 'Recommended Crops',
            fertilizerRecommendationTitle: 'Fertilizer Recommendations',
            newAnalysisText: 'New Analysis',
            currentLang: 'हिंदी',
            viewFertilizerText: 'View Detailed Fertilizer Report',
            locationModalTitle: 'Location Information Required',
            locationModalDesc: 'Please provide the missing location information to continue:',
            modalDistrictLabel: 'District',
            modalStateLabel: 'State',
            modalSubmitBtnText: 'Submit'
        },
        hindi: {
            pageTitle: 'मिट्टी रिपोर्ट विश्लेषण',
            pageDescription: 'अपनी मिट्टी के परैमीटर के आधार पर अनुकूलित फसल और उर्वरक सिफारिशें प्राप्त करने के लिए अपनी मिट्टी की रिपोर्ट अपलोड करें।',
            uploadTitle: 'मिट्टी रिपोर्ट अपलोड करें',
            uploadInstructions: 'कृपया विश्लेषण के लिए अपनी मिट्टी परीक्षण रिपोर्ट अपलोड करें या तस्वीर लें।',
            uploadTabText: 'रिपोर्ट अपलोड करें',
            cameraTabText: 'तस्वीर लें',
            uploadHint: 'अपनी मिट्टी की रिपोर्ट खींचें और छोड़ें या ब्राउज़ करने के लिए क्लिक करें',
            captureText: 'कैप्चर करें',
            switchCameraText: 'कैमरा बदलें',
            retakeText: 'फिर से लें',
            processText: 'मिट्टी रिपोर्ट संसाधित करें',
            processingText: 'आपकी मिट्टी रिपोर्ट संसाधित हो रही है...',
            pleaseWaitText: 'कृपया प्रतीक्षा करें, इसमें कुछ समय लग सकता है।',
            resultTitle: 'मिट्टी विश्लेषण परिणाम',
            soilParamsTitle: 'मिट्टी के पैरामीटर',
            locationInfoTitle: 'स्थान जानकारी',
            phLabel: 'पीएच स्तर',
            ecLabel: 'ईसी',
            ocLabel: 'जैविक कार्बन',
            phosphorusLabel: 'फॉस्फोरस',
            potassiumLabel: 'पोटैशियम',
            zincLabel: 'जिंक',
            copperLabel: 'कॉपर',
            ironLabel: 'आयरन',
            manganeseLabel: 'मैंगनीज',
            districtResultLabel: 'जिला',
            stateResultLabel: 'राज्य',
            recommendedCropsTitle: 'अनुशंसित फसलें',
            fertilizerRecommendationTitle: 'उर्वरक अनुशंसाएँ',
            newAnalysisText: 'नया विश्लेषण',
            currentLang: 'English',
            viewFertilizerText: 'विस्तृत उर्वरक रिपोर्ट देखें',
            locationModalTitle: 'स्थान की जानकारी आवश्यक है',
            locationModalDesc: 'जारी रखने के लिए कृपया अनुपलब्ध स्थान की जानकारी प्रदान करें:',
            modalDistrictLabel: 'जिला',
            modalStateLabel: 'राज्य',
            modalSubmitBtnText: 'जमा करें'
        }
    };

    // DOM Elements
    const uploadTabBtn = document.getElementById('uploadTabBtn');
    const cameraTabBtn = document.getElementById('cameraTabBtn');
    const uploadSection = document.getElementById('uploadSection');
    const cameraSection = document.getElementById('cameraSection');
    const reportUpload = document.getElementById('reportUpload');
    const uploadPreviewContainer = document.getElementById('uploadPreviewContainer');
    const uploadPreview = document.getElementById('uploadPreview');
    const cameraFeed = document.getElementById('cameraFeed');
    const captureBtn = document.getElementById('captureBtn');
    const switchCameraBtn = document.getElementById('switchCameraBtn');
    const cameraPreviewContainer = document.getElementById('cameraPreviewContainer');
    const cameraPreview = document.getElementById('cameraPreview');
    const retakeBtn = document.getElementById('retakeBtn');
    const processBtn = document.getElementById('processBtn');
    const languageToggle = document.getElementById('languageToggle');
    const currentLang = document.getElementById('currentLang');
    const inputForm = document.getElementById('inputForm');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.getElementById('resultContainer');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    const viewFertilizerBtn = document.getElementById('viewFertilizerBtn');
    
    // Create hidden input fields for district and state (since they're removed from the HTML)
    const districtInput = document.createElement('input');
    districtInput.type = 'hidden';
    districtInput.id = 'district';
    document.body.appendChild(districtInput);
    
    const stateInput = document.createElement('input');
    stateInput.type = 'hidden';
    stateInput.id = 'state';
    document.body.appendChild(stateInput);
    
    // Create location popup modal
    const modal = document.createElement('div');
    modal.id = 'locationModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h3 class="text-lg font-semibold text-gray-800 mb-4" id="locationModalTitle">
                Location Information Required
            </h3>
            <p class="text-gray-600 mb-4" id="locationModalDesc">
                Please provide the missing location information to continue:
            </p>
            <div id="modalDistrictField" class="mb-4 hidden">
                <label for="modalDistrict" class="block text-sm font-medium text-gray-700 mb-1" id="modalDistrictLabel">
                    District
                </label>
                <input type="text" id="modalDistrict" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" placeholder="Enter district name">
            </div>
            <div id="modalStateField" class="mb-4 hidden">
                <label for="modalState" class="block text-sm font-medium text-gray-700 mb-1" id="modalStateLabel">
                    State
                </label>
                <input type="text" id="modalState" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500" placeholder="Enter state name">
            </div>
            <div class="flex justify-center">
                <button id="modalSubmitBtn" class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors">
                    Submit
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Modal elements
    const locationModal = document.getElementById('locationModal');
    const modalDistrictField = document.getElementById('modalDistrictField');
    const modalStateField = document.getElementById('modalStateField');
    const modalDistrict = document.getElementById('modalDistrict');
    const modalState = document.getElementById('modalState');
    const modalSubmitBtn = document.getElementById('modalSubmitBtn');
    const locationModalTitle = document.getElementById('locationModalTitle');
    const locationModalDesc = document.getElementById('locationModalDesc');
    
    // Result fields
    const resultDate = document.getElementById('resultDate');
    const phValue = document.getElementById('phValue');
    const ecValue = document.getElementById('ecValue');
    const ocValue = document.getElementById('ocValue');
    const nitrogenValue = document.getElementById('nitrogenValue');
    const phosphorusValue = document.getElementById('phosphorusValue');
    const potassiumValue = document.getElementById('potassiumValue');
    const zincValue = document.getElementById('zincValue');
    const copperValue = document.getElementById('copperValue');
    const ironValue = document.getElementById('ironValue');
    const manganeseValue = document.getElementById('manganeseValue');
    const sulphurValue = document.getElementById('sulphurValue');
    const districtValue = document.getElementById('districtValue');
    const stateValue = document.getElementById('stateValue');
    const cropList = document.getElementById('cropList');
    const fertilizerRecommendation = document.getElementById('fertilizerRecommendation');
    
    // State variables
    let currentLanguage = 'english';
    let capturedImage = null;
    let uploadedFile = null;
    let videoStream = null;
    let facingMode = 'environment'; // Start with back camera
    let soilReportId = null;
    
    // Check if language is passed as URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('language')) {
        currentLanguage = urlParams.get('language');
        updateLanguage(currentLanguage);
    }
    
    // Initially disable the process button until a file is selected
    processBtn.disabled = true;
    
    // Apply translations function
    function applyTranslations(language) {
        const elements = document.querySelectorAll('[id]');
        const trans = translations[language];
        
        elements.forEach(element => {
            const key = element.id;
            if (trans[key]) {
                // If the element is an input placeholder
                if (element.placeholder) {
                    element.placeholder = trans[key];
                } else {
                    element.textContent = trans[key];
                }
            }
        });
        
        currentLanguage = language;
    }
    
    // Tab switching functionality
    uploadTabBtn.addEventListener('click', function() {
        uploadTabBtn.classList.add('active', 'bg-green-50', 'text-green-700', 'border-green-200');
        uploadTabBtn.classList.remove('bg-gray-50', 'text-gray-700', 'border-gray-200');
        
        cameraTabBtn.classList.remove('active', 'bg-green-50', 'text-green-700', 'border-green-200');
        cameraTabBtn.classList.add('bg-gray-50', 'text-gray-700', 'border-gray-200');
        
        uploadSection.classList.remove('hidden');
        cameraSection.classList.add('hidden');
        
        // Stop camera when switching to upload tab
        stopCamera();
    });
    
    cameraTabBtn.addEventListener('click', function() {
        cameraTabBtn.classList.add('active', 'bg-green-50', 'text-green-700', 'border-green-200');
        cameraTabBtn.classList.remove('bg-gray-50', 'text-gray-700', 'border-gray-200');
        
        uploadTabBtn.classList.remove('active', 'bg-green-50', 'text-green-700', 'border-green-200');
        uploadTabBtn.classList.add('bg-gray-50', 'text-gray-700', 'border-gray-200');
        
        cameraSection.classList.remove('hidden');
        uploadSection.classList.add('hidden');
        
        // Start camera when switching to camera tab
        startCamera();
    });
    
    // Language toggle functionality
    languageToggle.addEventListener('click', function() {
        const newLanguage = currentLanguage === 'english' ? 'hindi' : 'english';
        applyTranslations(newLanguage);
        
        // Update text of modal elements if modal is open
        if (!locationModal.classList.contains('hidden')) {
            if (locationModalTitle) {
                locationModalTitle.textContent = translations[newLanguage].locationModalTitle || 'Location Information Required';
            }
            
            if (locationModalDesc) {
                locationModalDesc.textContent = translations[newLanguage].locationModalDesc || 'Please provide the missing location information to continue:';
            }
            
            if (document.getElementById('modalDistrictLabel')) {
                document.getElementById('modalDistrictLabel').textContent = translations[newLanguage].modalDistrictLabel || 'District';
            }
            
            if (document.getElementById('modalStateLabel')) {
                document.getElementById('modalStateLabel').textContent = translations[newLanguage].modalStateLabel || 'State';
            }
            
            if (modalSubmitBtn) {
                modalSubmitBtn.textContent = translations[newLanguage].modalSubmitBtnText || 'Submit';
            }
        }
    });
    
    // File upload handling
    reportUpload.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            uploadedFile = e.target.files[0];
            console.log("File selected:", uploadedFile.name, "Type:", uploadedFile.type);
            
            // Check file size - restrict to 10MB
            const maxSize = 10 * 1024 * 1024; // 10MB in bytes
            if (uploadedFile.size > maxSize) {
                alert('The file is too large. Please upload a file smaller than 10MB.');
                reportUpload.value = ''; // Clear the file input
                uploadedFile = null;
                uploadPreviewContainer.style.display = 'none';
                processBtn.disabled = true;
                return;
            }
            
            // Get file extension
            const fileExt = uploadedFile.name.split('.').pop().toLowerCase();
            
            // Check if it's an image file
            if (uploadedFile.type.startsWith('image/')) {
                console.log("Processing as image");
                const reader = new FileReader();
                reader.onload = function(e) {
                    uploadPreview.src = e.target.result;
                    uploadPreviewContainer.style.display = 'block';
                    console.log("Image preview displayed");
                };
                reader.readAsDataURL(uploadedFile);
            } 
            // Check if it's a PDF
            else if (uploadedFile.type === 'application/pdf' || fileExt === 'pdf') {
                console.log("Processing as PDF");
                // Set PDF icon as placeholder while loading
                uploadPreview.src = '/static/images/pdf_icon.png';
                uploadPreviewContainer.style.display = 'block';
                
                // Read the PDF file
                const reader = new FileReader();
                reader.onload = function(e) {
                    const typedarray = new Uint8Array(e.target.result);
                    
                    // Load the PDF file using PDF.js
                    pdfjsLib.getDocument(typedarray).promise.then(function(pdf) {
                        // Get the first page
                        pdf.getPage(1).then(function(page) {
                            // Set scale for the PDF preview
                            const viewport = page.getViewport({ scale: 1.5 });
                            
                            // Create a canvas for rendering
                            const canvas = document.createElement('canvas');
                            const context = canvas.getContext('2d');
                            canvas.height = viewport.height;
                            canvas.width = viewport.width;
                            
                            // Render PDF page into canvas context
                            const renderContext = {
                                canvasContext: context,
                                viewport: viewport
                            };
                            
                            page.render(renderContext).promise.then(function() {
                                // Convert canvas to image
                                uploadPreview.src = canvas.toDataURL();
                                console.log("PDF preview displayed");
                            }).catch(function(error) {
                                console.error('Error rendering PDF page:', error);
                            });
                        }).catch(function(error) {
                            console.error('Error getting PDF page:', error);
                        });
                    }).catch(function(error) {
                        console.error('Error loading PDF:', error);
                    });
                };
                reader.readAsArrayBuffer(uploadedFile);
            }
            // Check for Word documents
            else if (uploadedFile.type === 'application/msword' || 
                     uploadedFile.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                     fileExt === 'doc' || fileExt === 'docx') {
                console.log("Processing as Word document");
                uploadPreview.src = '/static/images/word_icon.png';
                uploadPreviewContainer.style.display = 'block';
            }
            // Check for Excel files
            else if (uploadedFile.type === 'application/vnd.ms-excel' ||
                     uploadedFile.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                     fileExt === 'xls' || fileExt === 'xlsx') {
                console.log("Processing as Excel file");
                uploadPreview.src = '/static/images/excel_icon.png';
                uploadPreviewContainer.style.display = 'block';
            }
            // For other file types
            else {
                console.log("Processing as generic file");
                uploadPreview.src = '/static/images/file_icon.png';
                uploadPreviewContainer.style.display = 'block';
            }
            
            // Enable the process button
            processBtn.disabled = false;
            console.log("Process button enabled");
        }
    });
    
    // Camera handling functions
    async function startCamera() {
        try {
            if (videoStream) {
                videoStream.getTracks().forEach(track => track.stop());
            }
            
            const constraints = {
                video: {
                    facingMode: facingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };
            
            videoStream = await navigator.mediaDevices.getUserMedia(constraints);
            cameraFeed.srcObject = videoStream;
            cameraPreviewContainer.style.display = 'none';
        } catch (err) {
            console.error('Error accessing camera:', err);
            alert('Camera access denied or not available. Please grant permission or use file upload instead.');
            
            // Switch back to upload tab
            uploadTabBtn.click();
        }
    }
    
    function stopCamera() {
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
            videoStream = null;
        }
    }
    
    // Switch camera functionality
    switchCameraBtn.addEventListener('click', function() {
        facingMode = facingMode === 'environment' ? 'user' : 'environment';
        startCamera();
    });
    
    // Capture image functionality
    captureBtn.addEventListener('click', function() {
        if (!videoStream) return;
        
        const canvas = document.createElement('canvas');
        canvas.width = cameraFeed.videoWidth;
        canvas.height = cameraFeed.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(cameraFeed, 0, 0, canvas.width, canvas.height);
        
        // Convert to blob
        canvas.toBlob(function(blob) {
            capturedImage = blob;
            capturedImage.name = 'captured_image.jpg';
            
            // Display preview
            cameraPreview.src = canvas.toDataURL('image/jpeg');
            cameraPreviewContainer.style.display = 'block';
            
            // Enable the process button
            processBtn.disabled = false;
        }, 'image/jpeg', 0.95);
    });
    
    // Retake photo functionality
    retakeBtn.addEventListener('click', function() {
        cameraPreviewContainer.style.display = 'none';
        capturedImage = null;
        
        // Disable the process button if no file is uploaded
        if (!uploadedFile) {
            processBtn.disabled = true;
        }
    });
    
    // Process button functionality
    processBtn.addEventListener('click', async function() {
        console.log("Process button clicked");
        
        // Validate inputs
        if (!uploadedFile && !capturedImage) {
            alert('Please upload a soil report or take a picture first.');
            return;
        }
        
        console.log("Starting soil report processing");
        
        // Process the report directly - we'll try to extract location from the report
        await processReport('', '');
    });
    
    // Process report function
    async function processReport(district, state) {
        console.log("Processing report with district:", district, "state:", state);
        
        // Show loading indicator
        inputForm.style.display = 'none';
        loadingIndicator.classList.remove('hidden');
        console.log("Loading indicator shown");
        
        // Prepare form data
        const formData = new FormData();
        
        // Add the image file (either uploaded or captured)
        if (uploadedFile) {
            formData.append('soil_report', uploadedFile);
            console.log("Added uploaded file to form data:", uploadedFile.name);
        } else if (capturedImage) {
            formData.append('soil_report', capturedImage, 'captured_image.jpg');
            console.log("Added captured image to form data");
        }
        
        // Add location information
        formData.append('district', district);
        formData.append('state', state);
        formData.append('language', currentLanguage);
        console.log("Form data prepared with language:", currentLanguage);
        
        // Process with API call
        try {
            console.log("Sending API request to analyze soil report");
            const response = await fetch('/api/analyze_soil_report', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const result = await response.json();
                console.error("API error response:", result);
                throw new Error(result.error || `Server error: ${response.status}`);
            }
            
            const result = await response.json();
            console.log("API response received:", result);
            
            // Check for error in the result
            if (result.error) {
                console.error("Error in result:", result.error);
                throw new Error(result.error);
            }
            
            // Check if location information is missing
            if (result.missing_location) {
                console.log("Missing location information detected");
                
                // Hide loading indicator
                loadingIndicator.classList.add('hidden');
                inputForm.style.display = 'block';
                
                // Store extracted soil parameters in hidden inputs to reuse later
                const soilParamsInput = document.createElement('input');
                soilParamsInput.type = 'hidden';
                soilParamsInput.id = 'extracted_soil_params';
                soilParamsInput.value = JSON.stringify(result.soil_params || {});
                document.body.appendChild(soilParamsInput);
                
                const reportPathInput = document.createElement('input');
                reportPathInput.type = 'hidden';
                reportPathInput.id = 'report_path';
                reportPathInput.value = result.report_path || '';
                document.body.appendChild(reportPathInput);
                
                // Show the location modal to collect missing information
                showLocationModal(
                    result.location.district || '',
                    result.location.state || ''
                );
                return;
            }
            
            // Display results if all required information is available
            console.log("All info available, displaying results");
            displayResults(result);
        } catch (error) {
            console.error('Error processing soil report:', error);
            alert(error.message || "Error processing soil report. Please try again.");
            
            // Hide loading, show form again
            loadingIndicator.classList.add('hidden');
            inputForm.style.display = 'block';
        }
    }
    
    // Function to show the location modal
    function showLocationModal(district, state) {
        console.log("Showing location modal. District:", district, "State:", state);
        
        // Update modal fields based on what's missing
        if (!district) {
            modalDistrictField.classList.remove('hidden');
            modalDistrict.value = '';
            console.log("District field shown");
        } else {
            modalDistrictField.classList.add('hidden');
            modalDistrict.value = district;
            console.log("District field hidden, value set");
        }
        
        if (!state) {
            modalStateField.classList.remove('hidden');
            modalState.value = '';
            console.log("State field shown");
        } else {
            modalStateField.classList.add('hidden');
            modalState.value = state;
            console.log("State field hidden, value set");
        }
        
        // Update translations
        if (locationModalTitle) {
            locationModalTitle.textContent = translations[currentLanguage].locationModalTitle || 'Location Information Required';
        }
        
        if (locationModalDesc) {
            locationModalDesc.textContent = translations[currentLanguage].locationModalDesc || 'Please provide the missing location information to continue:';
        }
        
        if (document.getElementById('modalDistrictLabel')) {
            document.getElementById('modalDistrictLabel').textContent = translations[currentLanguage].modalDistrictLabel || 'District';
        }
        
        if (document.getElementById('modalStateLabel')) {
            document.getElementById('modalStateLabel').textContent = translations[currentLanguage].modalStateLabel || 'State';
        }
        
        if (modalSubmitBtn) {
            modalSubmitBtn.textContent = translations[currentLanguage].modalSubmitBtnText || 'Submit';
        }
        
        // Show the modal
        locationModal.classList.remove('hidden');
        console.log("Location modal displayed");
        
        // Focus the first input that's visible
        if (!district) {
            setTimeout(() => modalDistrict.focus(), 100);
        } else if (!state) {
            setTimeout(() => modalState.focus(), 100);
        }
    }
    
    // Display results function
    function displayResults(data) {
        // Hide loading indicator
        loadingIndicator.classList.add('hidden');
        // Set result date
        if (resultDate) {
            resultDate.textContent = new Date().toLocaleDateString();
        }
        // Show results
        resultContainer.style.display = 'block';
        
        // Set current date
        const now = new Date();
        const dateElement = document.getElementById('resultDate');
        if (dateElement) {
            dateElement.textContent = now.toLocaleDateString();
        }
        
        // Populate soil parameters
        const soilParams = data.soil_params || {};
        const elements = {
            'phValue': soilParams.ph ? soilParams.ph.toFixed(2) : 'N/A',
            'ecValue': soilParams.ec ? soilParams.ec.toFixed(2) : 'N/A',
            'ocValue': soilParams.organic_carbon ? soilParams.organic_carbon.toFixed(2) + '%' : 'N/A',
            'nitrogenValue': soilParams.nitrogen ? soilParams.nitrogen.toFixed(2) + ' kg/ha' : 'N/A',
            'phosphorusValue': soilParams.phosphorus ? soilParams.phosphorus.toFixed(2) + ' kg/ha' : 'N/A',
            'potassiumValue': soilParams.potassium ? soilParams.potassium.toFixed(2) + ' kg/ha' : 'N/A',
            'zincValue': soilParams.zinc ? soilParams.zinc.toFixed(2) + ' ppm' : 'N/A',
            'copperValue': soilParams.copper ? soilParams.copper.toFixed(2) + ' ppm' : 'N/A',
            'ironValue': soilParams.iron ? soilParams.iron.toFixed(2) + ' ppm' : 'N/A',
            'manganeseValue': soilParams.manganese ? soilParams.manganese.toFixed(2) + ' ppm' : 'N/A',
            'sulphurValue': soilParams.sulphur ? soilParams.sulphur.toFixed(2) + ' ppm' : 'N/A'
        };
        
        // Safely set element values
        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        }

        // Populate location info
        const location = data.location || {};
        const districtElement = document.getElementById('districtValue');
        const stateElement = document.getElementById('stateValue');
        
        if (districtElement) {
            districtElement.textContent = location.district || 'N/A';
        }
        
        if (stateElement) {
            stateElement.textContent = location.state || 'N/A';
        }
        
        // Handle crop recommendations
        const recommendations = data.recommendations || {};
        const crops = recommendations.crops || [];
        const cropListElement = document.getElementById('cropList');
        
        if (cropListElement) {
            // Clear previous crops
            cropListElement.innerHTML = '';
            
            // Add new crops
            crops.forEach((crop, index) => {
                const cropItem = document.createElement('div');
                cropItem.className = 'crop-item';
                
                // Make the first crop (best match) highlighted
                if (index === 0) {
                    cropItem.classList.add('primary-crop');
                    cropItem.innerHTML = `<i class="fa-solid fa-star text-yellow-500 mr-2"></i> ${crop}`;
                } else {
                    cropItem.innerHTML = `<i class="fa-solid fa-seedling text-green-500 mr-2"></i> ${crop}`;
                }
                
                cropListElement.appendChild(cropItem);
            });
        }
        
        // As requested, remove the fertilizer summary
        // We'll still keep the fertilizer recommendation but just make it minimal
        const fertRecommendationElement = document.getElementById('fertilizerRecommendation');
        if (fertRecommendationElement) {
            fertRecommendationElement.textContent = recommendations.fertilizer || 'No specific recommendations';
        }
        
        // Store the soil report ID for the fertilizer report link and update the button
        if (data.soil_report_id) {
            soilReportId = data.soil_report_id;
            
            // If viewFertilizerBtn exists, update its href and make it visible
            if (viewFertilizerBtn) {
                viewFertilizerBtn.href = `/fertilizer_report/${soilReportId}`;
                viewFertilizerBtn.style.display = 'inline-flex';
            }
        } else {
            // Hide the button if no report ID
            if (viewFertilizerBtn) {
                viewFertilizerBtn.style.display = 'none';
            }
        }
        
        // Add crop variety information if available
        if (data.crop_varieties) {
            // Create crop varieties section if it doesn't exist
            let cropVarietiesSection = document.getElementById('cropVarietiesSection');
            if (!cropVarietiesSection) {
                cropVarietiesSection = document.createElement('div');
                cropVarietiesSection.id = 'cropVarietiesSection';
                cropVarietiesSection.className = 'crop-varieties-section mt-6';
                resultContainer.appendChild(cropVarietiesSection);
            }
            
            // Clear previous content
            cropVarietiesSection.innerHTML = '';
            
            // Add header
            const header = document.createElement('h3');
            header.className = 'text-xl font-semibold text-green-800 mb-4';
            header.textContent = `${data.crop_varieties.crop_name.toUpperCase()} Recommended Varieties`;
            cropVarietiesSection.appendChild(header);

            // Check if varieties were found
            if (data.crop_varieties.found && data.crop_varieties.varieties && data.crop_varieties.varieties.length > 0) {
                // Create carousel container
                const carouselContainer = document.createElement('div');
                carouselContainer.className = 'variety-carousel';
                
                // Create carousel inner container
                const carouselInner = document.createElement('div');
                carouselInner.className = 'variety-carousel-inner';
                carouselContainer.appendChild(carouselInner);
                
                // Track carousel state
                let currentSlide = 0;
                const totalSlides = data.crop_varieties.varieties.length;
                let autoSlideInterval;
                
                // Add variety cards to carousel
                data.crop_varieties.varieties.forEach((variety, index) => {
                    const slide = document.createElement('div');
                    slide.className = 'variety-slide';
                    slide.dataset.index = index;
                    
                    // Create the variety card
                    const card = document.createElement('div');
                    card.className = 'variety-card';
                    
                    // Card header
                    const cardHeader = document.createElement('div');
                    cardHeader.className = 'variety-card-header';
                    cardHeader.textContent = variety.variety_name;
                    card.appendChild(cardHeader);
                    
                    // Card body
                    const cardBody = document.createElement('div');
                    cardBody.className = 'variety-card-body';
                    
                    // Key metrics section (simplified)
                    const metricsBox = document.createElement('div');
                    metricsBox.className = 'key-metrics';
                    
                    // Yield metric
                    const yieldMetric = document.createElement('div');
                    yieldMetric.className = 'metric';
                    yieldMetric.innerHTML = `
                        <div class="metric-value">${variety.yield}</div>
                        <div class="metric-label">Yield (q/acre)</div>
                    `;
                    metricsBox.appendChild(yieldMetric);
                    
                    // Maturity metric
                    const maturityMetric = document.createElement('div');
                    maturityMetric.className = 'metric';
                    maturityMetric.innerHTML = `
                        <div class="metric-value">${variety.maturity_days}</div>
                        <div class="metric-label">Maturity (Days)</div>
                    `;
                    metricsBox.appendChild(maturityMetric);
                    
                    cardBody.appendChild(metricsBox);
                    
                    // Key traits section (simplified)
                    const traitsSection = document.createElement('div');
                    traitsSection.className = 'key-traits';
                    traitsSection.innerHTML = `
                        <div class="traits-title">Key Traits</div>
                        <div class="traits-content">${variety.key_traits}</div>
                    `;
                    cardBody.appendChild(traitsSection);
                    
                    // Details toggle button
                    const detailsToggle = document.createElement('button');
                    detailsToggle.className = 'details-toggle';
                    detailsToggle.innerHTML = `
                        <span>Growing Details</span>
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    `;
                    cardBody.appendChild(detailsToggle);
                    
                    // Collapsible details content
                    const detailsContent = document.createElement('div');
                    detailsContent.className = 'details-content';
                    
                    // Growing details items
                    const detailsItems = [
                        { label: 'Soil Type', value: variety.soil_requirements },
                        { label: 'pH Range', value: variety.ph },
                        { label: 'Sowing', value: variety.sowing_time },
                        { label: 'Harvesting', value: variety.harvesting_time },
                        { label: 'Irrigation', value: `Every ${variety.irrigation_schedule} days` },
                        { label: 'Seed Rate', value: `${variety.seed_rate} kg/acre` }
                    ];
                    
                    detailsItems.forEach(item => {
                        const detailItem = document.createElement('div');
                        detailItem.className = 'details-item';
                        detailItem.innerHTML = `
                            <div class="details-label">${item.label}:</div>
                            <div class="details-value">${item.value}</div>
                        `;
                        detailsContent.appendChild(detailItem);
                    });
                    
                    // Fertilizer details section
                    const fertilizerDetails = document.createElement('div');
                    fertilizerDetails.className = 'fertilizer-details';
                    fertilizerDetails.innerHTML = `
                        <div class="details-item">
                            <div class="details-label">Unirrigated:</div>
                            <div class="details-value">${variety.fertilizer.unirrigated}</div>
                        </div>
                        <div class="details-item">
                            <div class="details-label">Irrigated (Early):</div>
                            <div class="details-value">${variety.fertilizer.irrigated_early}</div>
                        </div>
                        <div class="details-item">
                            <div class="details-label">Irrigated (Late):</div>
                            <div class="details-value">${variety.fertilizer.irrigated_late}</div>
                        </div>
                    `;
                    detailsContent.appendChild(fertilizerDetails);
                    
                    cardBody.appendChild(detailsContent);
                    
                    // Toggle details visibility on click
                    detailsToggle.addEventListener('click', function() {
                        const isHidden = detailsContent.style.display === 'none' || detailsContent.style.display === '';
                        detailsContent.style.display = isHidden ? 'block' : 'none';
                        
                        // Update arrow direction
                        const svg = detailsToggle.querySelector('svg path');
                        if (isHidden) {
                            svg.setAttribute('d', 'M5 15l7-7 7 7');
                        } else {
                            svg.setAttribute('d', 'M19 9l-7 7-7-7');
                        }
                    });
                    
                    card.appendChild(cardBody);
                    slide.appendChild(card);
                    carouselInner.appendChild(slide);
                });
                
                // Create carousel controls
                const controlsContainer = document.createElement('div');
                controlsContainer.className = 'carousel-controls';
                
                // Previous button
                const prevButton = document.createElement('button');
                prevButton.className = 'carousel-prev';
                prevButton.innerHTML = '&larr;';
                prevButton.disabled = true; // Start at first slide
                
                // Next button
                const nextButton = document.createElement('button');
                nextButton.className = 'carousel-next';
                nextButton.innerHTML = '&rarr;';
                if (totalSlides <= 1) nextButton.disabled = true;
                
                // Dots container
                const dotsContainer = document.createElement('div');
                dotsContainer.className = 'carousel-dots';
                
                // Add dots for each slide
                for (let i = 0; i < totalSlides; i++) {
                    const dot = document.createElement('div');
                    dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
                    dot.dataset.index = i;
                    
                    // Click on dot to go to slide
                    dot.addEventListener('click', function() {
                        goToSlide(parseInt(this.dataset.index));
                    });
                    
                    dotsContainer.appendChild(dot);
                }
                
                // Add controls to container
                controlsContainer.appendChild(prevButton);
                controlsContainer.appendChild(dotsContainer);
                controlsContainer.appendChild(nextButton);
                
                // Add controls to carousel
                carouselContainer.appendChild(controlsContainer);
                
                // Add carousel to section
                cropVarietiesSection.appendChild(carouselContainer);
                
                // Function to go to a specific slide
                function goToSlide(index) {
                    if (index < 0 || index >= totalSlides) return;
                    
                    // Update current slide
                    currentSlide = index;
                    
                    // Update carousel position
                    carouselInner.style.transform = `translateX(-${currentSlide * 100}%)`;
                    
                    // Update dots
                    const dots = dotsContainer.querySelectorAll('.carousel-dot');
                    dots.forEach((dot, i) => {
                        dot.classList.toggle('active', i === currentSlide);
                    });
                    
                    // Update button states
                    prevButton.disabled = currentSlide === 0;
                    nextButton.disabled = currentSlide === totalSlides - 1;
                    
                    // Reset auto-slide timer when manually changing slides
                    resetAutoSlide();
                }
                
                // Previous button click
                prevButton.addEventListener('click', function() {
                    goToSlide(currentSlide - 1);
                });
                
                // Next button click
                nextButton.addEventListener('click', function() {
                    goToSlide(currentSlide + 1);
                });
                
                // Function to start auto-sliding
                function startAutoSlide() {
                    stopAutoSlide(); // Clear any existing interval
                    
                    // Only auto-slide if there's more than one slide
                    if (totalSlides > 1) {
                        autoSlideInterval = setInterval(function() {
                            let nextSlide = currentSlide + 1;
                            if (nextSlide >= totalSlides) nextSlide = 0;
                            goToSlide(nextSlide);
                        }, 5000); // Change slide every 5 seconds
                    }
                }
                
                // Function to stop auto-sliding
                function stopAutoSlide() {
                    if (autoSlideInterval) {
                        clearInterval(autoSlideInterval);
                        autoSlideInterval = null;
                    }
                }
                
                // Function to reset auto-slide timer
                function resetAutoSlide() {
                    stopAutoSlide();
                    startAutoSlide();
                }
                
                // Start auto-sliding
                startAutoSlide();
                
                // Pause auto-sliding when mouse is over the carousel
                carouselContainer.addEventListener('mouseenter', stopAutoSlide);
                carouselContainer.addEventListener('mouseleave', startAutoSlide);
                
                // Add translation note for Hindi users
                const translationNote = document.createElement('div');
                translationNote.className = 'mt-4 text-sm text-gray-600 italic';
                translationNote.innerHTML = 'उपरोक्त फसल किस्मों की जानकारी आपके क्षेत्र के लिए अनुशंसित है। अधिक जानकारी के लिए स्थानीय कृषि विभाग से संपर्क करें।';
                cropVarietiesSection.appendChild(translationNote);
                
            } else {
                // No varieties found message
                const noVarietiesMsg = document.createElement('div');
                noVarietiesMsg.className = 'bg-yellow-50 p-4 rounded-lg text-yellow-800 border border-yellow-200';
                noVarietiesMsg.innerHTML = `No specific varieties found for ${data.crop_varieties.crop_name}. Please consult your local agricultural extension for recommendations.`;
                cropVarietiesSection.appendChild(noVarietiesMsg);
            }
        }
    }
    
    // New analysis button
    newAnalysisBtn.addEventListener('click', function() {
        // Reset form
        reportUpload.value = '';
        uploadPreviewContainer.style.display = 'none';
        uploadedFile = null;
        capturedImage = null;
        districtInput.value = '';
        stateInput.value = '';
        
        // Disable process button
        processBtn.disabled = true;
        
        // Hide results, show form
        resultContainer.style.display = 'none';
        inputForm.style.display = 'block';
        
        // Switch to upload tab
        uploadTabBtn.click();
    });
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        stopCamera();
    });
    
    // Initial translation application
    applyTranslations(currentLanguage);
    
    // Modal submit handler
    modalSubmitBtn.addEventListener('click', async function() {
        // Get values from the modal
        const district = modalDistrict.value.trim();
        const state = modalState.value.trim();
        
        // Validate that fields are not empty if they are visible
        const districtRequired = !modalDistrictField.classList.contains('hidden');
        const stateRequired = !modalStateField.classList.contains('hidden');
        
        let isValid = true;
        let errorMsg = "";
        
        if (districtRequired && !district) {
            isValid = false;
            errorMsg = currentLanguage === 'english' ? 
                "Please enter a district name." : 
                "कृपया जिले का नाम दर्ज करें।";
        } else if (stateRequired && !state) {
            isValid = false;
            errorMsg = currentLanguage === 'english' ? 
                "Please enter a state name." : 
                "कृपया राज्य का नाम दर्ज करें।";
        }
        
        if (!isValid) {
            alert(errorMsg);
            return;
        }
        
        // Hide the modal
        locationModal.classList.add('hidden');
        
        // Show loading indicator
        inputForm.style.display = 'none';
        loadingIndicator.classList.remove('hidden');
        
        // Get previously stored soil parameters and report path if they exist
        const soilParamsInput = document.getElementById('extracted_soil_params');
        const reportPathInput = document.getElementById('report_path');
        
        // If this is a continuation of an earlier process, 
        // we can optimize by using the stored soil parameters
        if (soilParamsInput && reportPathInput && reportPathInput.value) {
            // This is a second step where we're just providing missing location
            try {
                const storedSoilParams = JSON.parse(soilParamsInput.value || '{}');
                const reportPath = reportPathInput.value;
                
                // Prepare request data
                const requestData = {
                    soil_params: storedSoilParams,
                    district: district,
                    state: state,
                    language: currentLanguage,
                    report_path: reportPath
                };
                
                // Send the request to the new endpoint
                console.log("Submitting location data to complete soil analysis");
                const response = await fetch('/api/complete_soil_analysis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (!response.ok) {
                    const errorResult = await response.json();
                    throw new Error(errorResult.error || `Server error: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Clean up the temp storage
                if (soilParamsInput) document.body.removeChild(soilParamsInput);
                if (reportPathInput) document.body.removeChild(reportPathInput);
                
                // Display results
                displayResults(result);
            } catch (error) {
                console.error('Error completing soil report analysis:', error);
                alert(error.message || "Error completing the analysis. Please try again.");
                
                // Hide loading, show form again
                loadingIndicator.classList.add('hidden');
                inputForm.style.display = 'block';
            }
        } else {
            // If we don't have stored data (shouldn't happen), process from scratch
            await processReport(district, state);
        }
    });
    
    // Also handle Enter key in the modal inputs
    modalDistrict.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            if (!modalStateField.classList.contains('hidden')) {
                modalState.focus();
            } else {
                modalSubmitBtn.click();
            }
        }
    });
    
    modalState.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            modalSubmitBtn.click();
        }
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !locationModal.classList.contains('hidden')) {
            locationModal.classList.add('hidden');
        }
    });
}); 