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

                const response = await fetch(`http://127.0.0.1:5050/searchDoctors?${query}`);
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
        async confirmBooking() {

            if (!this.selectedDoctor || !this.modalSelectedTime) {
                alert("Please select a doctor and time.");
                return;
            }
            
            if (!this.selectedDoctor || !this.modalSelectedTime) {
                alert("Please select a doctor and time.");
                return;
            }
        
            const patientData = JSON.parse(sessionStorage.getItem("patient"));
        
            const dateStr = this.selectedDate;
            const timeStr = this.modalSelectedTime;
        
            const payload = {
                patient_id: patientData?.id,
                doctor_id: this.selectedDoctor?.Doctor_ID,
                doctor_name: this.selectedDoctor?.Doctor_Name,
                appointment_date: dateStr,
                start_time: `${dateStr}T${timeStr}`,
                end_time: `${dateStr}T${this.addOneHour(timeStr)}`,
                notes: this.reason
            };
        
            console.log("📦 Payload:", payload); // Debug logging
        
            try {
                const response = await fetch("http://127.0.0.1:5050/createAppointment", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
        
                const result = await response.json();
        
                if (response.ok && result.code === 201) {
                    alert("✅ Appointment booked successfully!");
                    this.searchDoctors(); // Refresh availability
        
                    // ✅ Hide modal after success
                    const modalElement = document.getElementById('bookingModal');
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    modal?.hide();
                } else {
                    alert(`❌ Failed to book appointment: ${result.message || 'Unknown error'}`);
                }
        
            } catch (err) {
                console.error("❌ Booking error:", err);
                alert("❌ Failed to book appointment. Server error.");
            }
        },
        addOneHour(timeStr) {
            const [hour, minute] = timeStr.split(":").map(Number);
            const newHour = (hour + 1).toString().padStart(2, "0");
            return `${newHour}:${minute.toString().padStart(2, "0")}:00`;
        }
    },
    computed: {
        filteredDoctors() {
            return this.doctors.filter(doc => doc.timeslots && doc.timeslots.length > 0);
        }
    }
});
vm = app.mount('#app');