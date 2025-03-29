const app = Vue.createApp({
    data() {
        return {
            selectedSpeciality: 'Any',
            selectedLocation: 'Any',
            selectedTime: '08:00',
            selectedDate: new Date().toISOString().split('T')[0],
            specialities: [],
            locations: [],
            doctors: [],
            availabilities: [],
            times: ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "13:00", "14:00", "15:00", "16:00",],  // default start

            // 🔥 Required for modal
            selectedDoctor: null,
            modalSelectedTime: null,
            availableTimesForModal: [],
            reason: '',
            sendReminders: true,
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
            const formattedDate = new Date(this.selectedDate).toISOString().split("T")[0];
            try {
                const res = await fetch(`http://104.214.186.4:5000/doctor_availabilities?date=${formattedDate}`);

                let availabilityData = [];
                if (res.ok) {
                    const data = await res.json();
                    availabilityData = data?.data || [];
                } else {
                    console.warn("⚠️ No availabilities found (non-200 response)");
                }

                this.availabilities = availabilityData;

                // Filter + map doctor times
                this.doctors = this.doctors.map(doc => {
                    const matchesSpec = this.selectedSpeciality === 'Any' || doc.Specialization === this.selectedSpeciality;
                    const matchesLoc = this.selectedLocation === 'Any' || doc.Polyclinic === this.selectedLocation;

                    if (matchesSpec && matchesLoc) {
                        const slots = availabilityData
                            .filter(a => a.DoctorID === doc.Doctor_ID && a.Available)
                            .map(a => a.StartTime);
                        return { ...doc, timeslots: slots };
                    } else {
                        return { ...doc, timeslots: [] };
                    }
                });

            } catch (err) {
                console.error("❌ Error fetching availabilities:", err);
                this.availabilities = [];
            }
        },
        formatTime(time24) {
            const [hour, minute] = time24.split(":");
            const h = parseInt(hour);
            const suffix = h >= 12 ? "PM" : "AM";
            const hour12 = h % 12 === 0 ? 12 : h % 12;
            return `${hour12}:${minute} ${suffix}`;
        },
        selectAppointment(doctor, time) {
            this.selectedDoctor = doctor;
            this.modalSelectedTime = time; // use modal variable
            this.availableTimesForModal = doctor.timeslots || [];
        },

        confirmBooking() {
            if (!this.selectedDoctor || !this.selectedTime) {
                alert("Please select a doctor and time.");
                return;
            }

            const booking = {
                doctorId: this.selectedDoctor.Doctor_ID,
                doctorName: this.selectedDoctor.Doctor_Name,
                specialization: this.selectedDoctor.Specialization,
                location: this.selectedDoctor.Polyclinic,
                date: this.selectedDate,
                time: this.selectedTime,
                reason: this.reason,
                sendReminders: this.sendReminders
            };

            console.log("Booking submitted:", booking);
            alert("✅ Booking confirmed!");
            // optionally send to backend...
        },
        selectAppointment(doctor) {
            this.selectedDoctor = doctor;
            this.modalSelectedTime = doctor.timeslots?.[0] || null; // default to first available time
            this.availableTimesForModal = doctor.timeslots || [];

            // Open modal via JS after state is ready
            const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
            modal.show();
        }
    },
    computed: {
        filteredDoctors() {
            return this.doctors.filter(doc => doc.timeslots && doc.timeslots.length > 0);
        }
    }
});

app.mount('#app');