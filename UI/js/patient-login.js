const patientURL = 'http://127.0.0.1:5001/patient';
const doctorURL = 'http://127.0.0.1:5010/doctor';

const app = Vue.createApp({
    data() {
        return {
            email: '',
            password: '',
            wrong: false,
            error: '',
            passwordVisible: false,
            role: 'patient'
        }
    },

    methods: {
        checkLogin() {
            // Check if the user is logged in
            let user = JSON.parse(sessionStorage.getItem(this.role)); // Dynamically check for role
            if (user != null) {
                // Redirect based on the role
                if (this.role === 'patient') {
                    window.location.href = './patientProfile.html';
                } else if (this.role === 'doctor') {
                    window.location.href = './doctorDashboard.html';
                }
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
            const loginURL = this.role === 'patient' ? patientURL + '/login' : doctorURL + '/login';
            
            axios.post(loginURL, params)
                .then((response) => {
                    let user = response.data.data;
                    // Add it into the session storage
                    console.log(user)
                    sessionStorage.setItem(this.role, JSON.stringify(user));
                    // Redirect to the appropriate profile page
                    if (this.role === 'patient') {
                        window.location.href = './patientProfile.html';
                    } else if (this.role === 'doctor') {
                        window.location.href = './doctorDashboard.html';
                    }
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