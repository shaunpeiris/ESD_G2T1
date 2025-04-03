const patientURL = 'http://127.0.0.1:5001/patient';

const app = Vue.createApp({
    data() {
        return {
            // Form data
            firstName: '',
            lastName: '',
            email: '',
            password: '',
            confirmPassword: '',
            mobile: '',  // Added mobile field
            dob: '',
            termsAgreed: false,
            
            // Form validation and UI
            formErrors: {},
            passwordVisible: false,
            confirmPasswordVisible: false,
            isSubmitting: false,
            submitSuccess: false,
            submitError: '',
            
            // Redirecting
            redirectCountdown: 5
        }
    },

    computed: {
        fullName() {
            return `${this.firstName} ${this.lastName}`.trim();
        },
        
        isFormValid() {
            return this.email && 
                   this.password && 
                   this.firstName && 
                   this.lastName && 
                   this.mobile &&  // Added mobile to form validation
                   this.password === this.confirmPassword && 
                   this.password.length >= 8 && 
                   this.termsAgreed;
        }
    },

    methods: {
        validateForm() {
            this.formErrors = {};
            let isValid = true;
            
            // Validate first name
            if (!this.firstName.trim()) {
                this.formErrors.firstName = 'First name is required';
                isValid = false;
            }
            
            // Validate last name
            if (!this.lastName.trim()) {
                this.formErrors.lastName = 'Last name is required';
                isValid = false;
            }
            
            // Validate email
            if (!this.email) {
                this.formErrors.email = 'Email address is required';
                isValid = false;
            } else if (!this.validateEmail(this.email)) {
                this.formErrors.email = 'Please enter a valid email address';
                isValid = false;
            }
            
            // Validate mobile number
            if (!this.mobile) {
                this.formErrors.mobile = 'Mobile number is required';
                isValid = false;
            } else if (!this.validateMobile(this.mobile)) {
                this.formErrors.mobile = 'Please enter a valid mobile number (digits only)';
                isValid = false;
            }
            
            // Validate password
            if (!this.password) {
                this.formErrors.password = 'Password is required';
                isValid = false;
            } else if (this.password.length < 8) {
                this.formErrors.password = 'Password must be at least 8 characters long';
                isValid = false;
            }
            
            // Validate password confirmation
            if (this.password !== this.confirmPassword) {
                this.formErrors.confirmPassword = 'Passwords do not match';
                isValid = false;
            }
            
            // Validate terms agreement
            if (!this.termsAgreed) {
                this.formErrors.terms = 'You must agree to the terms and conditions';
                isValid = false;
            }
            
            return isValid;
        },
        
        validateEmail(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },
        
        validateMobile(mobile) {
            // Validate that mobile contains only digits
            const re = /^\d+$/;
            return re.test(mobile);
        },
        
        togglePasswordVisibility(field) {
            if (field === 'password') {
                this.passwordVisible = !this.passwordVisible;
            } else if (field === 'confirmPassword') {
                this.confirmPasswordVisible = !this.confirmPasswordVisible;
            }
        },
        
        async submitForm() {
            if (!this.validateForm()) {
                // Apply is-invalid classes to form elements with errors
                for (const field in this.formErrors) {
                    const element = document.getElementById(field);
                    if (element) {
                        element.classList.add('is-invalid');
                    }
                }
                return;
            }
            
            this.isSubmitting = true;
            this.submitError = '';
            
            try {
                // Prepare the user data
                const userData = {
                    name: this.fullName,
                    email: this.email,
                    mobile: this.mobile,  // Added mobile to user data
                    password: this.password,
                    medicalHistory: {
                        allergies: [],
                        medical_conditions: [],
                        past_surgeries: [],
                        family_medical_history: [],
                        chronic_illnesses: [],
                        medications: []
                    }
                };
                
                // Send request to create the user
                const response = await axios.post(`${patientURL}/create`, userData);
                
                if (response.data.code === 201) {
                    // Success! Clear the form
                    this.submitSuccess = true;
                    
                    // Set a countdown to redirect to login
                    this.startRedirectCountdown();
                } else {
                    this.submitError = response.data.message || 'Failed to create account';
                }
            } catch (error) {
                console.error('Signup error:', error);
                if (error.response && error.response.data) {
                    this.submitError = error.response.data.message || 'Error creating account';
                } else {
                    this.submitError = 'Error connecting to the server. Please try again later.';
                }
            } finally {
                this.isSubmitting = false;
            }
        },
        
        clearInvalidClass(field) {
            const element = document.getElementById(field);
            if (element) {
                element.classList.remove('is-invalid');
            }
            if (this.formErrors[field]) {
                delete this.formErrors[field];
            }
        },
        
        startRedirectCountdown() {
            this.redirectCountdown = 5;
            const countdownInterval = setInterval(() => {
                this.redirectCountdown--;
                if (this.redirectCountdown <= 0) {
                    clearInterval(countdownInterval);
                    window.location.href = 'patientLogin.html';
                }
            }, 1000);
        }
    }
});

app.mount('#signup-form');