const logoutApp = Vue.createApp({
    data() {
        return {};
    },
    methods: {
        logout() {
            const roles = ['patient', 'doctor', 'pharmacy'];
            let userFound = false;

            for (const role of roles) {
                const user = JSON.parse(sessionStorage.getItem(role));
                if (user) {
                    console.log(`Logging out ${role}:`, user.Email || user.name || 'User');
                    sessionStorage.removeItem(role);
                    userFound = true;
                    break;
                }
            }

            if (!userFound) {
                console.log('No user found in sessionStorage.');
            }

            // Redirect to a common login page or customize based on role
            window.location.href = './index.html';
        }
    }
});

// Mount the app to the element with id="signout"
logoutApp.mount('#signout');