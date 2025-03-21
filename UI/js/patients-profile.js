const patientURL = 'http://localhost:5000/patient';

const app = Vue.createApp({
    data() {
        return {
            patient: null,
            medicalHistory: {
                allergies: [],
                medical_conditions: '',
                past_surgeries: '',
                family_medical_history: '',
                chronic_illnesses: '',
                medications: ''
            },
            newAllergy: '',
            saveMessage: false,
            errorMessage: '',
            showError: false,
            bloodTypes: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
            selectedBloodType: '',
            height: '',
            weight: '',
            currentPassword: '',
            newPassword: '',
            confirmPassword: '',
            activeTab: 'personal'
        }
    },

    methods: {
        checkLogin() {
            // Check if the user is logged in
            const patientData = sessionStorage.getItem('patient');
            if (!patientData) {
                window.location.href = 'login.html';
                return;
            }
            
            this.patient = JSON.parse(patientData);
            
            // Set up medical history from patient data
            if (this.patient.medicalHistory) {
                this.medicalHistory = this.patient.medicalHistory;
                
                // Convert array-based items to strings for textarea fields
                if (Array.isArray(this.medicalHistory.medical_conditions)) {
                    this.medicalHistory.medical_conditions = this.medicalHistory.medical_conditions.join(', ');
                }
                if (Array.isArray(this.medicalHistory.past_surgeries)) {
                    this.medicalHistory.past_surgeries = this.medicalHistory.past_surgeries.join(', ');
                }
                if (Array.isArray(this.medicalHistory.family_medical_history)) {
                    this.medicalHistory.family_medical_history = this.medicalHistory.family_medical_history.join(', ');
                }
                if (Array.isArray(this.medicalHistory.chronic_illnesses)) {
                    this.medicalHistory.chronic_illnesses = this.medicalHistory.chronic_illnesses.join(', ');
                }
                if (Array.isArray(this.medicalHistory.medications)) {
                    this.medicalHistory.medications = this.medicalHistory.medications.join(', ');
                }
            } else {
                // Initialize empty medical history
                this.medicalHistory = {
                    allergies: [],
                    medical_conditions: '',
                    past_surgeries: '',
                    family_medical_history: '',
                    chronic_illnesses: '',
                    medications: ''
                };
            }
        },
        
        savePersonalInfo() {
            // In a real implementation, this would send updated data to the server
            this.showSaveMessage();
        },
        
        addAllergy() {
            if (this.newAllergy.trim()) {
                if (!this.medicalHistory.allergies) {
                    this.medicalHistory.allergies = [];
                }
                this.medicalHistory.allergies.push(this.newAllergy.trim());
                this.newAllergy = '';
            }
        },
        
        removeAllergy(index) {
            this.medicalHistory.allergies.splice(index, 1);
        },
        
        saveMedicalInfo() {
            // Convert text fields to arrays where needed
            let updatedMedicalHistory = {
                allergies: this.medicalHistory.allergies,
                medical_conditions: this.stringToArray(this.medicalHistory.medical_conditions),
                past_surgeries: this.stringToArray(this.medicalHistory.past_surgeries),
                family_medical_history: this.stringToArray(this.medicalHistory.family_medical_history),
                chronic_illnesses: this.stringToArray(this.medicalHistory.chronic_illnesses),
                medications: this.stringToArray(this.medicalHistory.medications)
            };
            
            // Send update to server
            axios.put(`${patientURL}/update`, {
                id: this.patient.id,
                medicalHistory: updatedMedicalHistory
            })
            .then(response => {
                // Update session storage with new data
                this.patient.medicalHistory = response.data.data.medicalHistory;
                sessionStorage.setItem('patient', JSON.stringify(this.patient));
                this.showSaveMessage();
            })
            .catch(error => {
                this.errorMessage = "Failed to update medical information.";
                this.showError = true;
                setTimeout(() => this.showError = false, 3000);
            });
        },
        
        updatePassword() {
            if (this.newPassword !== this.confirmPassword) {
                this.errorMessage = "Passwords do not match.";
                this.showError = true;
                setTimeout(() => this.showError = false, 3000);
                return;
            }
            
            // In a real implementation, this would verify current password and update with new one
            this.showSaveMessage();
            
            // Clear password fields after save
            this.currentPassword = '';
            this.newPassword = '';
            this.confirmPassword = '';
        },
        
        togglePasswordVisibility(inputId, event) {
            const passwordInput = document.getElementById(inputId);
            const icon = event.currentTarget.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            }
        },
        
        stringToArray(str) {
            if (!str) return [];
            return str.split(',')
                .map(item => item.trim())
                .filter(item => item.length > 0);
        },
        
        showSaveMessage() {
            this.saveMessage = true;
            setTimeout(() => this.saveMessage = false, 3000);
        },
        
        setActiveTab(tab) {
            this.activeTab = tab;
        },
        
        logout() {
            sessionStorage.removeItem('patient');
            window.location.href = 'login.html';
        }
    },
    
    created() {
        this.checkLogin();
    }
});

app.mount('#profile-app');