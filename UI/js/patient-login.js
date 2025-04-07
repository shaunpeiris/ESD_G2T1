const patientURL = 'http://127.0.0.1:5001/patient';

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
            let user = JSON.parse(sessionStorage.getItem(this.role));
            if (user != null) {
                window.location.href = './patientProfile.html';
            }
        },

        login(event) {
            if (event) event.preventDefault();

            const loginURL = patientURL + '/login';

            axios.post(loginURL, {
                email: this.email,
                password: this.password
            })
            .then((response) => {
                const user = response.data.data;
                sessionStorage.setItem(this.role, JSON.stringify(user));
                window.location.href = './patientProfile.html';
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
});

app.mount('#login');
