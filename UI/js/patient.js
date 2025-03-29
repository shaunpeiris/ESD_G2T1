const app = Vue.createApp({
    data() {
        return {
            selectedSpeciality: 'Any',
            selectedLocation: 'Any',
            selectedDate: new Date().toISOString().split('T')[0],
            specialities: [],
            locations: [],
            doctors: [],

            // Modal stuff
            selectedDoctor: null,
            modalSelectedTime: null,
            availableTimesForModal: [],
            reason: '',
            sendReminders: true
        };
    },
    mounted() {
        this.fetchSpecializations();
        this.fetchPolyclinics();
    },
    methods: {
        async fetchSpecializations() {
            const res = await fetch('http://104.214.186.4:5010/specializations');
            const data = await res.json();
            this.specialities = ['Any', ...data.data];
        },
        async fetchPolyclinics() {
            const res = await fetch('http://104.214.186.4:5010/polyclinics');
            const data = await res.json();
            this.locations = ['Any', ...data.data];
        },
        async searchDoctors() {
            try {
                const query = new URLSearchParams({
                    specialization: this.selectedSpeciality,
                    polyclinic: this.selectedLocation,
                    date: this.selectedDate
                }).toString();
        
                const response = await fetch(`http://localhost:5050/searchDoctors?${query}`);
                const data = await response.json();
        
                if (data.data && Array.isArray(data.data)) {
                    this.doctors = data.data.map(doc => ({
                        ...doc,
                        timeslots: doc.timeslots || []
                    }));
                } else {
                    this.doctors = [];
                    console.warn("Empty or invalid doctor list from API.");
                }
        
            } catch (err) {
                console.error("❌ Error fetching doctors:", err);
                this.doctors = [];
            }
        },
        formatTime(time24) {
            const [hour, minute] = time24.split(":");
            const h = parseInt(hour);
            const suffix = h >= 12 ? "PM" : "AM";
            const hour12 = h % 12 === 0 ? 12 : h % 12;
            return `${hour12}:${minute} ${suffix}`;
        },
        selectAppointment(doctor) {
            this.selectedDoctor = doctor;
            this.availableTimesForModal = doctor.timeslots || [];  // ✅ fix here
            this.modalSelectedTime = this.availableTimesForModal[0] || null;
        
            const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
            modal.show();
        },
        confirmBooking() {
            if (!this.selectedDoctor || !this.modalSelectedTime) {
                alert("Please select a doctor and time.");
                return;
            }

            const booking = {
                doctorId: this.selectedDoctor.Doctor_ID,
                doctorName: this.selectedDoctor.Doctor_Name,
                specialization: this.selectedDoctor.Specialization,
                location: this.selectedDoctor.Polyclinic,
                date: this.selectedDate,
                time: this.modalSelectedTime,
                reason: this.reason,
                sendReminders: this.sendReminders
            };

            console.log("✅ Booking confirmed:", booking);
            alert("✅ Booking confirmed!");
        }
    },
    computed: {
        filteredDoctors() {
            return this.doctors.filter(doc => doc.timeslots && doc.timeslots.length > 0);
        }
    }
});
vm = app.mount('#app');