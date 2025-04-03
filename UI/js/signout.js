const logoutApp = Vue.createApp({
    data() {
        return {
            // We don't need any data properties for this simple component
        }
    },

    methods: {
        // Logout function that will be called when the button is clicked
        logout() {
            // Check if the user is logged in
            const patient = JSON.parse(sessionStorage.getItem('patient'));
            console.log('Logging out user:', patient ? patient.name : 'No user found');
            
            // Clear the session storage
            sessionStorage.removeItem('patient');
            
            // Redirect to login page
            window.location.href = './patientLogin.html';
        }
    }
});

// Mount the app to the element with id="signout"
logoutApp.mount('#signout');