const patientURL = 'http://localhost:5000/patient';

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

        login() {
            let params = {
                email: this.email,
                password: this.password
            }
            
            loginURL = patientURL + '/login';
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
                    this.error = error.response.data.message || "Login failed. Please check your credentials.";
                })
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