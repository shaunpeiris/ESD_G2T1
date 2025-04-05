const pharmacistURL = 'http://104.214.186.4:5020/pharmacy';

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
                window.location.href = './pharmacist.html';
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
                window.location.href = './pharmacist.html';
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