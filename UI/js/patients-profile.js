// // Patient edit details page for pharmacy system - Refactored to use only pharmacy routes
// const pharmacyURL = 'http://localhost:8000/pharmacy';

// const app = Vue.createApp({
//     data() {
//         return {
//             prescriptionId: null,
//             issueType: null,
//             patient: {
//                 id: null,
//                 name: '',
//                 email: '',
//                 mobile: ''
//             },
//             saveMessage: false,
//             errorMessage: '',
//             showError: false,
//             activeTab: 'personal',
//             loading: true,
//             invalidFields: {
//                 email: false,
//                 mobile: false
//             }
//         }
//     },

//     methods: {
//         loadPatientData() {
//             // Parse URL parameters
//             const urlParams = new URLSearchParams(window.location.search);
//             this.prescriptionId = urlParams.get('prescription');
//             this.issueType = urlParams.get('issue') || 'billing';

//             if (!this.prescriptionId) {
//                 this.showError = true;
//                 this.errorMessage = 'No prescription ID provided. Cannot load patient data.';
//                 this.loading = false;
//                 return;
//             }

//             console.log(`Attempting to fetch prescription data for ID: ${this.prescriptionId}`);

//             // Step 1: Get prescription data
//             fetch(`${pharmacyURL}/prescription/${this.prescriptionId}`)
//                 .then(response => {
//                     if (!response.ok) {
//                         const errorMsg = `Prescription API Error (${response.status}): ${response.statusText}`;
//                         console.error(errorMsg);
//                         throw new Error(errorMsg);
//                     }
//                     return response.json();
//                 })
//                 .then(response => {
//                     // Get appointment ID from prescription
//                     const prescriptionData = response.data;
//                     if (!prescriptionData) {
//                         throw new Error('API returned empty prescription data');
//                     }

//                     if (!prescriptionData.appointment_id) {
//                         throw new Error(`Prescription ${this.prescriptionId} has no associated appointment_id`);
//                     }

//                     console.log(`Found appointment ID: ${prescriptionData.appointment_id}`);

//                     // Step 2: Get appointment data which contains patient info
//                     return fetch(`${pharmacyURL}/appointment/${prescriptionData.appointment_id}`)
//                         .then(appResponse => {
//                             if (!appResponse.ok) {
//                                 const errorMsg = `Appointment API Error (${appResponse.status}): ${appResponse.statusText}`;
//                                 console.error(errorMsg);
//                                 throw new Error(errorMsg);
//                             }
//                             return appResponse.json();
//                         })
//                         .then(appointmentResponse => {
//                             // Extract patient data from appointment response
//                             if (!appointmentResponse.data) {
//                                 throw new Error('API returned empty appointment data');
//                             }

//                             const appointmentData = appointmentResponse.data;

//                             // Step 3: Extract patient information from the appointment
//                             if (!appointmentData.patient_id) {
//                                 throw new Error('Appointment has no associated patient_id');
//                             }

//                             // After getting the patient ID from appointment data
//                             const patientId = appointmentData.patient_id;

//                             // Use the new dedicated endpoint to get complete patient info
//                             return fetch(`${pharmacyURL}/patient/${patientId}`)
//                                 .then(response => {
//                                     if (!response.ok) {
//                                         const errorMsg = `Patient API Error (${response.status}): ${response.statusText}`;
//                                         console.error(errorMsg);
//                                         throw new Error(errorMsg);
//                                     }
//                                     return response.json();
//                                 })
//                                 .then(response => {
//                                     if (response.code !== 200 || !response.data) {
//                                         throw new Error(response.message || 'Failed to retrieve patient data');
//                                     }

//                                     // Use the complete patient data directly
//                                     this.patient = {
//                                         id: response.data.id,
//                                         name: response.data.name || 'Unknown Patient',
//                                         email: response.data.email || '',
//                                         mobile: response.data.mobile || ''
//                                     };

//                                     console.log(`Successfully loaded complete patient data for: ${this.patient.name}`);

//                                     // Now that we have the patient ID, we can use the dispense endpoint
//                                     // to attempt to get more details - by making a mock call
//                                     // This is a workaround since there's no patient endpoint

//                                     // Call dispense with a special header to indicate we just want info
//                                     const mockHeaders = new Headers({
//                                         'X-Mode': 'info-only',
//                                         'Content-Type': 'application/json'
//                                     });

//                                     return fetch(`${pharmacyURL}/dispense/${this.prescriptionId}`, {
//                                         method: 'POST',
//                                         headers: mockHeaders
//                                     })
//                                         .then(response => {
//                                             // Even if this fails, we already have basic patient info
//                                             // so we can still proceed with the form
//                                             if (response.ok) {
//                                                 return response.json()
//                                                     .then(dispenseData => {
//                                                         // Check if we got patient email and phone
//                                                         if (dispenseData.data && dispenseData.data.patient_info) {
//                                                             if (dispenseData.data.patient_info.email) {
//                                                                 this.patient.email = dispenseData.data.patient_info.email;
//                                                             }
//                                                             if (dispenseData.data.patient_info.mobile ||
//                                                                 dispenseData.data.patient_info.phone_number) {
//                                                                 this.patient.mobile = dispenseData.data.patient_info.mobile ||
//                                                                     dispenseData.data.patient_info.phone_number;
//                                                             }
//                                                         }

//                                                         console.log(`Successfully loaded enhanced patient data`);
//                                                     })
//                                                     .catch(error => {
//                                                         console.warn('Could not parse dispense data but proceeding with basic info');
//                                                         console.warn(error);
//                                                     });
//                                             }
//                                             // If this fails, just continue with what we have
//                                             return Promise.resolve();
//                                         })
//                                         .catch(error => {
//                                             console.warn('Additional patient data fetch failed but proceeding with basic info');
//                                             console.warn(error);
//                                             return Promise.resolve();
//                                         });
//                                 });
//                         });
//                 })
//                 .then(() => {
//                     this.loading = false;
//                     this.highlightProblemField();
//                 })
//                 .catch(error => {
//                     console.error('Error loading patient data:', error);

//                     // Provide detailed error messages based on the error type
//                     let detailedError = error.message;

//                     if (error.message.includes('prescription')) {
//                         detailedError = `Failed to retrieve prescription #${this.prescriptionId}: ${error.message}`;
//                     } else if (error.message.includes('appointment')) {
//                         detailedError = `Failed to retrieve appointment data: ${error.message}`;
//                     } else if (error.message.includes('patient')) {
//                         detailedError = `Failed to retrieve patient information: ${error.message}`;
//                     }

//                     // Check for network errors
//                     if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
//                         detailedError = `Network error: Please check your connection and ensure the API server is running at ${pharmacyURL}`;
//                     }

//                     this.showError = true;
//                     this.errorMessage = detailedError;
//                     this.loading = false;
//                 });
//         },

//         highlightProblemField() {
//             // Determine which fields are invalid based on the issue type
//             this.invalidFields = {
//                 email: this.issueType === 'email',
//                 mobile: this.issueType === 'phone'
//             };

//             // Add visual indication to the problematic field
//             setTimeout(() => {
//                 if (this.invalidFields.email) {
//                     const emailField = document.getElementById('email');
//                     if (emailField) {
//                         emailField.classList.add('border-danger');
//                         emailField.focus();
//                     }
//                 } else if (this.invalidFields.mobile) {
//                     const phoneField = document.getElementById('mobile');
//                     if (phoneField) {
//                         phoneField.classList.add('border-danger');
//                         phoneField.focus();
//                     }
//                 }
//             }, 100);
//         },

//         savePersonalInfo() {
//             // Validate email
//             if (!this.patient.email || !this.validateEmail(this.patient.email)) {
//                 this.errorMessage = "Please enter a valid email address.";
//                 this.showError = true;
//                 setTimeout(() => this.showError = false, 3000);
//                 return;
//             }

//             // Validate phone number
//             if (!this.patient.mobile || !this.validatePhone(this.patient.mobile)) {
//                 this.errorMessage = "Please enter a valid phone number.";
//                 this.showError = true;
//                 setTimeout(() => this.showError = false, 3000);
//                 return;
//             }

//             // Prepare update data
//             const updateData = {
//                 id: this.patient.id,
//                 name: this.patient.name,
//                 email: this.patient.email,
//                 mobile: this.patient.mobile
//             };

//             // Send update to server using the pharmacy endpoint
//             fetch(`${pharmacyURL}/update-patient`, {
//                 method: 'PUT',
//                 headers: {
//                     'Content-Type': 'application/json',
//                 },
//                 body: JSON.stringify(updateData)
//             })
//                 .then(response => {
//                     if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//                     return response.json();
//                 })
//                 .then(response => {
//                     if (response.code !== 200) {
//                         throw new Error(response.message || 'Failed to update patient information');
//                     }

//                     this.saveMessage = true;

//                     // Redirect back to pharmacy page after showing success message
//                     if (this.prescriptionId) {
//                         setTimeout(() => {
//                             // Specifically redirect to pharmacy page if we came from there
//                             if (document.referrer.includes('pharmacy.html')) {
//                                 window.location.href = document.referrer;
//                             } else {
//                                 window.location.href = 'http://localhost:8080/views/pharmacist.html';
//                             }
//                         }, 2000);
//                     }
//                 })
//                 .catch(error => {
//                     console.error('Error updating patient:', error);
//                     this.errorMessage = `Failed to update patient information: ${error.message}`;
//                     this.showError = true;
//                     setTimeout(() => this.showError = false, 3000);
//                 });
//         },

//         validateEmail(email) {
//             const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
//             return re.test(email);
//         },

//         validatePhone(phone) {
//             // Basic validation - adjust based on your requirements
//             return phone && phone.length >= 8;
//         },

//         setActiveTab(tab) {
//             this.activeTab = tab;
//         },

//         showGlobalError(message) {
//             this.errorMessage = message;
//             this.showError = true;
//             setTimeout(() => this.showError = false, 5000);
//         },

//         logout() {
//             window.location.href = document.referrer || 'index.html';
//         }
//     },

//     created() {
//         this.loadPatientData();
//     }
// });

// app.mount('#profile-app');
