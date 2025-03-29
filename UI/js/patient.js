const app = Vue.createApp({
    data() {
        return {
            selectedSpeciality: 'Any',
            selectedLocation: 'Any',
            selectedDate: new Date().toISOString().split('T')[0],
            specialities: [],
            locations: [],
            doctors: [],
            availabilities: [],
        };
    },
    mounted() {
        this.fetchSpecializations();
        this.fetchDoctors();
        this.fetchPolyclinics();
    },
    methods: {
        async fetchSpecializations() {
            const res = await fetch('http://104.214.186.4:5010/specializations');
            const data = await res.json();
            this.specialities = ['Any', ...data.data];
        },
        async fetchDoctors() {
            const res = await fetch('http://104.214.186.4:5010/doctors');
            const data = await res.json();
            this.doctors = data.data;
        },
        async fetchPolyclinics() {
            const res = await fetch('http://104.214.186.4:5010/polyclinics');
            const data = await res.json();
            this.locations = ['Any', ...data.data];
        },
        async searchDoctors() {
            // Step 1: Fetch availability for selected date
            const formattedDate = new Date(this.selectedDate).toISOString().split("T")[0];
            const res = await fetch(`http://104.214.186.4:5000/doctor_availabilities?date=${formattedDate}`);
            const data = await res.json();
            this.availabilities = data.data;

            // Step 2: Build doctor list with available time slots
            this.doctors = this.doctors.map(doc => {
                const matchesSpec = this.selectedSpeciality === 'Any' || doc.Specialization === this.selectedSpeciality;
                const matchesLoc = this.selectedLocation === 'Any' || doc.Polyclinic === this.selectedLocation;

                if (matchesSpec && matchesLoc) {
                    const slots = this.availabilities
                        .filter(a => a.DoctorID === doc.Doctor_ID && a.Available)
                        .map(a => a.StartTime);
                    return { ...doc, timeslots: slots };
                } else {
                    return { ...doc, timeslots: [] };
                }
            });
        },
        formatTime(time24) {
            const [hour, minute] = time24.split(":");
            const h = parseInt(hour);
            const suffix = h >= 12 ? "PM" : "AM";
            const hour12 = h % 12 === 0 ? 12 : h % 12;
            return `${hour12}:${minute} ${suffix}`;
        }
    },
    computed: {
        filteredDoctors() {
            return this.doctors.filter(doc => doc.timeslots && doc.timeslots.length > 0);
        }
    }
});

app.mount('#app');