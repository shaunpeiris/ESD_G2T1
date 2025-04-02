const pharmacistURL = 'http://104.214.186.4:5015/pharmacy'; // Adjust port if needed

const app = Vue.createApp({
    data() {
        return {
            email: '',
            password: '',
            wrong: false,
            error: '',
            passwordVisible: false,
            role: 'pharmacy'
        }
    },

    methods: {
        checkLogin() {
            let user = JSON.parse(sessionStorage.getItem(this.role));
            if (user != null) {
                window.location.href = './pharmacistDashboard.html';
            }
        },

        login(event) {
            if (event) event.preventDefault();

            const loginURL = pharmacistURL + '/login';

            axios.post(loginURL, {
                email: this.email,
                password: this.password
            })
            .then((response) => {
                const user = response.data.data;
                sessionStorage.setItem(this.role, JSON.stringify(user));
                window.location.href = './pharmacistDashboard.html';
            })
            .catch((error) => {
                this.wrong = true;
                this.error = (error.response?.data?.message) || "Login failed. Please check your credentials.";
                console.error("Login error:", error);
            });
        },

        togglePasswordVisibility() {
            this.passwordVisible = !this.passwordVisible;
        }
    },

    created() {
        this.checkLogin();
    }

    methods: {
        // Logout function that will be called when the button is clicked
        logout() {
            // Check if the user is logged in
            const patient = JSON.parse(sessionStorage.getItem('patient'));
            console.log('Logging out user:', patient ? patient.name : 'No user found');
            
            // Clear the session storage
            sessionStorage.removeItem('patient');
            
            // Redirect to login page
            window.location.href = './login.html';
        }
    }
});

app.mount('#login');