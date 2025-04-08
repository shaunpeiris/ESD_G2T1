// Pharmacy management interface - Optimized
// Global variables and helper functions defined at the top
let allPrescriptions = { pending: [], completed: [] };

// Helper formatters defined early to prevent "not defined" errors
const formatDate = dateStr => {
    if (!dateStr) return 'Unknown Date';
    try {
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric', month: 'long', day: 'numeric'
        });
    } catch {
        return 'Invalid Date Format';
    }
};

const formatProcessingStatus = status => {
    if (!status) return 'Unknown';
    return status.split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

document.addEventListener('DOMContentLoaded', () => {
    // Create notification container
    document.body.appendChild(Object.assign(document.createElement('div'), {
        id: 'errorNotification',
        className: 'toast-container position-fixed top-0 end-0 p-3',
        style: 'zIndex: 1100'
    }));
    
    // Add spinner animation style
    document.head.appendChild(Object.assign(document.createElement('style'), {
        textContent: '@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}.spin{animation:spin 1s linear infinite}'
    }));
    
    loadPrescriptionData();
    setupEventListeners();
});

// Notification system
function showNotification(message, type = 'Error', duration = 5000) {
    const container = document.getElementById('errorNotification');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.id = 'toast-' + Date.now();
    
    const isError = type === 'Error';
    toast.innerHTML = `
      <div class="toast-header bg-${isError ? 'danger' : 'success'} text-white">
        <i class="bi bi-${isError ? 'exclamation-circle-fill' : 'check-circle-fill'} me-2"></i>
        <strong class="me-auto">${type}</strong>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">${message}</div>
    `;

    container.appendChild(toast);
    if (isError) console.error(`${type}: ${message}`);
    if (duration) setTimeout(() => document.getElementById(toast.id)?.remove(), duration);
}

const showError = (msg, title = 'Error', duration = 5000) => showNotification(msg, title, duration);
const showSuccess = (msg, title = 'Success', duration = 5000) => showNotification(msg, title, duration);

// Load prescriptions data
function loadPrescriptionData() {
    const pendingContainer = document.getElementById('pending-prescriptions');
    const completedContainer = document.getElementById('completed-prescriptions');
    const loadingHtml = '<div class="col-12 text-center p-3"><div class="spinner-border spin text-primary"></div><p>Loading prescriptions...</p></div>';
    
    [pendingContainer, completedContainer].forEach(container => {
        if (container) container.innerHTML = loadingHtml;
    });

    fetch('http://localhost:8000/pharmacy/prescriptions')
        .then(response => response.ok ? response.json() : Promise.reject(new Error(`HTTP error! Status: ${response.status}`)))
        .then(prescriptions => {
            // Normalize status values and split by status
            const processedPrescriptions = prescriptions.map(p => ({
                ...p,
                status: p.status === true || p.status === 'true' || p.status === 'completed' ? 'completed' : 'pending'
            }));
            
            // Store all prescriptions for search functionality
            allPrescriptions.pending = processedPrescriptions.filter(p => p.status === 'pending');
            allPrescriptions.completed = processedPrescriptions.filter(p => p.status === 'completed');
            
            // Update counter badges
            document.querySelector('#pending-tab .badge').textContent = allPrescriptions.pending.length;
            document.querySelector('#completed-tab .badge').textContent = allPrescriptions.completed.length;
            
            // Apply any existing search filter
            applySearch();
        })
        .catch(error => {
            console.error('Error loading prescriptions:', error);
            const errorHtml = `<div class="col-12"><div class="alert alert-danger">Error loading prescriptions: ${error.message}</div></div>`;
            
            [pendingContainer, completedContainer].forEach(container => {
                if (container) container.innerHTML = errorHtml;
            });
            
            showError(`Failed to load prescription data: ${error.message}`);
        });
}

// Search function
function applySearch() {
    const searchTerm = document.getElementById('prescriptionSearch')?.value.trim().toLowerCase();
    
    // If no search term, show all prescriptions
    if (!searchTerm) {
        displayPrescriptionsInTab('pending-prescriptions', allPrescriptions.pending, true);
        displayPrescriptionsInTab('completed-prescriptions', allPrescriptions.completed, false);
        return;
    }
    
    // Filter prescriptions by name or ID
    const filteredPending = allPrescriptions.pending.filter(p => 
        (p.patientName && p.patientName.toLowerCase().includes(searchTerm)) || 
        (p.id && p.id.toString().includes(searchTerm)) ||
        (p.prescriptionNumber && p.prescriptionNumber.toString().includes(searchTerm))
    );
    
    const filteredCompleted = allPrescriptions.completed.filter(p => 
        (p.patientName && p.patientName.toLowerCase().includes(searchTerm)) || 
        (p.id && p.id.toString().includes(searchTerm)) ||
        (p.prescriptionNumber && p.prescriptionNumber.toString().includes(searchTerm))
    );

    // Display filtered results
    displayPrescriptionsInTab('pending-prescriptions', filteredPending, true);
    displayPrescriptionsInTab('completed-prescriptions', filteredCompleted, false);
    
    // Update counter badges with filtered counts
    document.querySelector('#pending-tab .badge').textContent = filteredPending.length;
    document.querySelector('#completed-tab .badge').textContent = filteredCompleted.length;
    
    // Show search results message if nothing found
    const totalResults = filteredPending.length + filteredCompleted.length;
    if (totalResults === 0) {
        showNotification(`No prescriptions found matching "${searchTerm}"`, 'Search Results', 3000);
    }
}

// Display prescription cards
function displayPrescriptionsInTab(tabContainerId, prescriptions, isPending) {
    const container = document.getElementById(tabContainerId);
    if (!container) return;

    container.innerHTML = '';

    // Show message if no prescriptions found
    if (prescriptions.length === 0) {
        const statusText = isPending ? 'pending' : 'completed';
        container.innerHTML = `<div class="col-12"><div class="alert alert-info">No ${statusText} prescriptions found</div></div>`;
        return;
    }

    // Create prescription cards
    prescriptions.forEach(prescription => {
        const cardClasses = `card prescription-card h-100 ${isPending ? (prescription.isUrgent ? 'urgent' : '') : 'completed'}`;
        const statusBadge = isPending ? 
            (prescription.isUrgent ? '<span class="badge bg-danger">Urgent</span>' : '<span class="badge bg-primary">Pending</span>') : 
            '<span class="badge bg-success">Completed</span>';
            
        const actionButton = isPending ?
            `<button class="btn btn-primary btn-sm w-100 process-prescription" data-prescription-id="${prescription.id}">
                <i class="bi bi-check2-circle me-2"></i>Process
            </button>` :
            `<button class="btn btn-info btn-sm w-100 view-details text-white" data-prescription-id="${prescription.id}">
                <i class="bi bi-eye me-2"></i>View Details
            </button>`;

        const cardCol = document.createElement('div');
        cardCol.className = 'col-lg-4 col-md-6 mb-3';
        cardCol.innerHTML = `
            <div class="${cardClasses}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="card-title mb-0">${prescription.patientName || 'Unknown Patient'}</h5>
                        ${statusBadge}
                    </div>
                    <h6 class="card-subtitle text-muted mb-2">Prescription #${prescription.prescriptionNumber || prescription.id}</h6>
                    <p class="card-text mb-1"><strong>Date:</strong> ${prescription.date ? new Date(prescription.date).toLocaleDateString() : 'Unknown date'}</p>
                    <p class="card-text mb-3"><strong>Items:</strong> ${prescription.medicationCount || 0} medications</p>
                </div>
                <div class="card-footer bg-transparent">
                    ${actionButton}
                </div>
            </div>
        `;

        container.appendChild(cardCol);
    });

    // Add event listeners for buttons
    container.querySelectorAll(isPending ? '.process-prescription' : '.view-details').forEach(button => {
        button.addEventListener('click', function() {
            const prescriptionId = this.getAttribute('data-prescription-id');
            openModal(prescriptionId, isPending);
        });
    });
}

// Open modal with appropriate mode
function openModal(prescriptionId, isProcessing) {
    const modal = document.getElementById('prescriptionProcessingModal');
    const modalBody = modal?.querySelector('.modal-body');
    if (!modal || !modalBody) return;
    
    // Show loading state
    modalBody.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="min-height: 200px;">
            <div class="text-center">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-3">Loading prescription details...</p>
            </div>
        </div>`;
    
    // Update modal title and footer based on mode
    const modalTitle = document.getElementById('prescriptionProcessingModalLabel');
    if (modalTitle) {
        modalTitle.textContent = isProcessing ? `Process Prescription #${prescriptionId}` : `Prescription Details #${prescriptionId}`;
        modalTitle.setAttribute('data-prescription-id', prescriptionId);
    }
    
    // Update footer based on mode
    const modalFooter = modal.querySelector('.modal-footer');
    if (modalFooter) {
        modalFooter.innerHTML = isProcessing ? 
            `<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
             <button type="button" class="btn btn-success" id="completeDispenseBtn">
                <i class="bi bi-bag-check me-2"></i>Complete & Dispense
             </button>` :
            `<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>`;
    }
    
    // Show modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Fetch prescription details
    fetch(`http://localhost:8000/pharmacy/prescription/${prescriptionId}`)
        .then(response => response.ok ? response.json() : Promise.reject(new Error(`HTTP error! Status: ${response.status}`)))
        .then(response => {
            modalBody.innerHTML = `
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h6>Prescription Details</h6>
                        <div class="card">
                            <div class="card-body" id="prescription-details"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>Pharmacy Notes</h6>
                        <div class="card">
                            <div class="card-body" id="pharmacy-notes"></div>
                        </div>
                    </div>
                </div>
                <h6>Medication ${isProcessing ? 'Verification' : 'List'}</h6>
                <div class="card mb-4">
                    <div class="card-body">
                        <div id="medicationList"></div>
                        ${isProcessing ? 
                            `<div class="alert alert-danger mb-3" id="inventoryAlert" style="display: none;">
                                <h6 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>Inventory Issues</h6>
                                <p class="mb-0"></p>
                            </div>` : ''}
                    </div>
                </div>
            `;
            
            updatePrescriptionDetails(response.data);
            if (response.data.pharmacy_info) updatePharmacyNotes(response.data.pharmacy_info);
            
            // Display medications differently based on mode
            const medications = response.data.medicine || [];
            isProcessing ? updateMedicationList(medications) : displayCompletedMedications(medications);
        })
        .catch(error => {
            console.error('Error fetching prescription details:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <h5 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>Error</h5>
                    <p>${error.message || 'Failed to load prescription details'}</p>
                </div>`;
            showError(error.message || 'Failed to load prescription details');
        });
}

// Shortcuts for modal opening
const openProcessingModal = prescriptionId => openModal(prescriptionId, true);
const openPrescriptionDetails = prescriptionId => openModal(prescriptionId, false);

// Display medications for completed prescriptions
function displayCompletedMedications(medications) {
    const medicationList = document.getElementById('medicationList');
    if (!medicationList) return;

    medicationList.innerHTML = !medications || medications.length === 0 ?
        '<p class="text-muted">No medications found in this prescription</p>' :
        medications.map(med => `
            <div class="rounded border p-3 mb-3 medication-item">
                <div class="row">
                    <div class="col">
                        <h5>${med.name}</h5>
                        <p class="mb-1"><strong>Instructions:</strong> ${med.instructions || 'Take as directed'}</p>
                        <p class="mb-1"><strong>Quantity:</strong> ${med.quantity} ${med.unit || 'units'}</p>
                    </div>
                </div>
            </div>
        `).join('');
}

// Update prescription details
function updatePrescriptionDetails(prescription) {
    const detailsSection = document.getElementById('prescription-details');
    if (!detailsSection) return;

    detailsSection.innerHTML = `
        <p class="mb-1"><strong>Prescription ID:</strong> ${prescription.prescription_id}</p>
        <p class="mb-1"><strong>Appointment ID:</strong> ${prescription.appointment_id || 'Not available'}</p>
        <p class="mb-1"><strong>Status:</strong> ${prescription.status ? 'Completed' : 'Pending'}</p>
        <p class="mb-1"><strong>Medications:</strong> ${Array.isArray(prescription.medicine) ? prescription.medicine.length : 0}</p>
    `;
}

// Display pharmacy notes
function updatePharmacyNotes(pharmacyInfo) {
    const notesSection = document.getElementById('pharmacy-notes');
    if (!notesSection) return;

    notesSection.innerHTML = !pharmacyInfo ? 
        '<p class="text-muted">No pharmacy notes available</p>' : 
        `<p class="mb-1"><strong>Processing Status:</strong> ${formatProcessingStatus(pharmacyInfo.processing_status)}</p>
         <p class="mb-1"><strong>Estimated Pickup:</strong> ${formatDate(pharmacyInfo.estimated_pickup_time)}</p>
         <p class="mb-1"><strong>Notes:</strong></p>
         <p class="fst-italic">${pharmacyInfo.pharmacy_notes || 'No specific notes provided.'}</p>`;
}

// Update medication list with inventory checking
function updateMedicationList(medications) {
    const medicationList = document.getElementById('medicationList');
    if (!medicationList) return;

    if (!medications || medications.length === 0) {
        medicationList.innerHTML = '<p class="text-muted">No medications found in this prescription</p>';
        return;
    }

    // Show loading indicator
    medicationList.innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">Checking inventory for ${medications.length} medications...</p>
        </div>`;

    // Fetch inventory data for all medications in parallel
    const insufficientStock = [];
    Promise.all(
        medications.map(med => 
            fetch(`http://localhost:8000/pharmacy/inventory/${encodeURIComponent(med.name)}`)
                .then(response => response.json())
                .catch(() => ({ error: true }))
        )
    )
    .then(inventoryResults => {
        medicationList.innerHTML = '';
        
        medications.forEach((med, index) => {
            const inventoryData = inventoryResults[index];
            const stockStatus = getStockStatus(med, inventoryData);
            
            // Create medication item
            const medicationItem = document.createElement('div');
            medicationItem.className = `rounded border p-3 mb-3 medication-item ${stockStatus.statusClass}`;
            medicationItem.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <h5>${med.name}</h5>
                        <p class="mb-1"><strong>Instructions:</strong> ${med.instructions || 'Take as directed'}</p>
                        <p class="mb-1"><strong>Quantity:</strong> ${med.quantity} ${med.unit || 'units'}</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <span class="badge ${stockStatus.badgeClass} mb-2">${stockStatus.label}</span>
                        ${stockStatus.insufficient ? 
                            `<div class="alert alert-warning py-1 px-2 text-small">
                                Need: ${med.quantity}, Available: ${stockStatus.available}
                            </div>` : ''}
                    </div>
                </div>`;
            
            medicationList.appendChild(medicationItem);
            
            // Track inventory issues
            if (stockStatus.insufficient) {
                insufficientStock.push({
                    name: med.name,
                    required: med.quantity,
                    available: stockStatus.available
                });
            }
        });
        
        // Update inventory alert
        updateInventoryAlert(insufficientStock);
    })
    .catch(error => {
        medicationList.innerHTML = `
            <div class="alert alert-danger">
                <h5 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>Error</h5>
                <p>Failed to check inventory: ${error.message || 'Unknown error'}</p>
            </div>`;
    });
}

// Get stock status for a medication
function getStockStatus(med, inventoryData) {
    let available = 0;
    let badgeClass = 'bg-secondary';
    let label = 'Unknown';
    let statusClass = '';
    let insufficient = true;
    
    if (inventoryData && !inventoryData.error) {
        const medications = inventoryData.Medications || [];
        const medication = medications[0] || {};
        available = medication.quantity || 0;
        
        if (available >= med.quantity) {
            badgeClass = 'bg-success';
            label = 'In Stock';
            statusClass = 'available';
            insufficient = false;
        } else if (available > 0) {
            badgeClass = 'bg-warning text-dark';
            label = 'Low Stock';
            statusClass = 'low-stock';
        } else {
            badgeClass = 'bg-danger';
            label = 'Out of Stock';
            statusClass = 'out-of-stock';
        }
    }
    
    return { available, badgeClass, label, statusClass, insufficient };
}

// Update inventory alert and button state
function updateInventoryAlert(insufficientStock) {
    const alertEl = document.getElementById('inventoryAlert');
    const dispenseBtn = document.getElementById('completeDispenseBtn');
    
    if (!alertEl || !dispenseBtn) return;
    
    if (insufficientStock.length > 0) {
        alertEl.style.display = 'block';
        alertEl.querySelector('p').innerHTML = insufficientStock.map(item => 
            `<strong>${item.name}</strong>: Need ${item.required}, only ${item.available} available`
        ).join('<br>');
        
        dispenseBtn.disabled = true;
        dispenseBtn.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>Insufficient Stock';
    } else {
        alertEl.style.display = 'none';
        dispenseBtn.disabled = false;
        dispenseBtn.innerHTML = '<i class="bi bi-bag-check me-2"></i>Complete & Dispense';
    }
}

// Process prescription
function dispensePrescription(prescriptionId) {
    const dispenseBtn = document.getElementById('completeDispenseBtn');
    
    // Check if button is disabled due to insufficient stock
    if (dispenseBtn && dispenseBtn.disabled) {
        showError('Cannot dispense: Insufficient stock for one or more medications');
        return;
    }
    
    // Show processing spinner
    if (dispenseBtn) {
        dispenseBtn.disabled = true;
        dispenseBtn.innerHTML = '<i class="bi bi-hourglass-split spin me-2"></i>Processing...';
    }

    fetch(`http://localhost:8000/pharmacy/dispense/${prescriptionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.ok ? response.json() : Promise.reject(new Error(`HTTP error! Status: ${response.status}`)))
    .then(response => {
        if (response.code >= 400) {
            showError(response.message || 'Failed to dispense prescription');
            return;
        }
        
        // Check notification status
        const data = response.data || {};
        if (!data.sms_notification_sent || !data.email_notification_sent) {
            let notificationMsg = "Warning: Some notifications failed to send.";
            if (!data.sms_notification_sent) notificationMsg += " SMS notification failed.";
            if (!data.email_notification_sent) notificationMsg += " Email notification failed.";
            showNotification(notificationMsg, 'Warning', 8000);
        }
        
        showSuccess(response.message || 'Prescription dispensed successfully');
        
        // Close modal and refresh data
        const modal = bootstrap.Modal.getInstance(document.getElementById('prescriptionProcessingModal'));
        if (modal) modal.hide();
        loadPrescriptionData();
    })
    .catch(error => {
        console.error('Error dispensing prescription:', error);
        showError('Failed to dispense prescription: ' + error.message);
    })
    .finally(() => {
        // Reset button state
        if (dispenseBtn) {
            dispenseBtn.disabled = false;
            dispenseBtn.innerHTML = '<i class="bi bi-bag-check me-2"></i>Complete & Dispense';
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    // Tab change handler
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', () => {
            const activeTabId = tabEl.getAttribute('data-bs-target').substring(1);
            document.getElementById(activeTabId).classList.add('show', 'active');
        });
    });
    
    // Search input handler with debounce
    const searchInput = document.getElementById('prescriptionSearch');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(applySearch, 300);
        });
        
        // Press Enter to search immediately
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(debounceTimer);
                applySearch();
            }
        });
    }
    
    // Clear search button
    const clearSearchBtn = document.getElementById('clearSearch');
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            const searchInput = document.getElementById('prescriptionSearch');
            if (searchInput) {
                searchInput.value = '';
                applySearch();
            }
        });
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refreshPrescriptions');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="bi bi-arrow-clockwise spin me-1"></i> Refreshing...';
            
            // Clear search when refreshing
            const searchInput = document.getElementById('prescriptionSearch');
            if (searchInput) searchInput.value = '';
            
            loadPrescriptionData();
            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i> Refresh';
            }, 1000);
        });
    }
    
    // Dispense button - Using event delegation
    document.body.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'completeDispenseBtn') {
            const modalTitle = document.getElementById('prescriptionProcessingModalLabel');
            if (!modalTitle) return showError('Could not determine which prescription to dispense');
            
            const match = modalTitle.textContent.match(/#(\d+)/);
            if (!match || !match[1]) return showError('Could not determine prescription ID');
            
            dispensePrescription(match[1]);
        }
    });
}
