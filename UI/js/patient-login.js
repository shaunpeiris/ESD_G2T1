const patientURL = 'http://127.0.0.1:5001/patient';

const app = Vue.createApp({
    data() {
        return {
            email: '',
            password: '',
            wrong: false,
            error: '',
            passwordVisible: false  
        }
    },

    methods: {
        checkLogin() {
            // Check if the user is logged in
            let patient = JSON.parse(sessionStorage.getItem('patient'));
            if (patient != null) {
                window.location.href = './patientProfile.html';
            }
        },

        login(event) {
            // Prevent the default form submission behavior
            if (event) event.preventDefault();
            
            let params = {
                email: this.email,
                password: this.password
            }
            
            // Make sure this variable is properly defined with 'const' or 'let'
            const loginURL = patientURL + '/login';
            
            axios.post(loginURL, params)
                .then((response) => {
                    let patient = response.data.data;
                    // Add it into the session storage
                    sessionStorage.setItem('patient', JSON.stringify(patient));
                    // Redirect to the patient profile page
                    window.location.href = './patientProfile.html';
                })
                .catch((error) => {
                    this.wrong = true;
                    // Set a default error message if the server response doesn't contain one
                    this.error = (error.response && error.response.data && error.response.data.message) 
                        ? error.response.data.message 
                        : "Login failed. Please check your credentials.";
                    console.error("Login error:", error);
                });
        },
        
        togglePasswordVisibility() {
            this.passwordVisible = !this.passwordVisible;
        },
    },

    created() {
        this.checkLogin();
    }
}); 

app.mount('#login');