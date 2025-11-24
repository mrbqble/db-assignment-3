--
-- PostgreSQL database dump
--

\restrict ocEQQs2ul5eMu4zgrjW5YcXbA92kWcxzMLwlVB1zBHpcNv0bdwHpchlHdNucNO2

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

-- Started on 2025-11-24 23:36:48

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 223 (class 1259 OID 29447)
-- Name: address; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.address (
    member_user_id integer NOT NULL,
    house_number character varying(10) NOT NULL,
    street character varying(100) NOT NULL,
    town character varying(100) NOT NULL
);


ALTER TABLE public.address OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 29501)
-- Name: appointment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.appointment (
    appointment_id integer NOT NULL,
    caregiver_user_id integer NOT NULL,
    member_user_id integer NOT NULL,
    appointment_date date NOT NULL,
    appointment_time time without time zone NOT NULL,
    work_hours numeric(4,1) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    CONSTRAINT check_appointment_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'accepted'::character varying, 'declined'::character varying])::text[]))),
    CONSTRAINT check_work_hours_positive CHECK ((work_hours > (0)::numeric))
);


ALTER TABLE public.appointment OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 29500)
-- Name: appointment_appointment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.appointment_appointment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.appointment_appointment_id_seq OWNER TO postgres;

--
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 227
-- Name: appointment_appointment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.appointment_appointment_id_seq OWNED BY public.appointment.appointment_id;


--
-- TOC entry 221 (class 1259 OID 29419)
-- Name: caregiver; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.caregiver (
    caregiver_user_id integer NOT NULL,
    photo character varying(255),
    gender character varying(10),
    caregiving_type character varying(50) NOT NULL,
    hourly_rate numeric(6,2) NOT NULL,
    CONSTRAINT check_caregiving_type CHECK (((caregiving_type)::text = ANY ((ARRAY['babysitter'::character varying, 'caregiver for elderly'::character varying, 'playmate for children'::character varying])::text[]))),
    CONSTRAINT check_hourly_rate_positive CHECK ((hourly_rate > (0)::numeric))
);


ALTER TABLE public.caregiver OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 29462)
-- Name: job; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.job (
    job_id integer NOT NULL,
    member_user_id integer NOT NULL,
    required_caregiving_type character varying(50) NOT NULL,
    other_requirements text,
    date_posted date DEFAULT CURRENT_DATE NOT NULL,
    CONSTRAINT check_required_caregiving_type CHECK (((required_caregiving_type)::text = ANY ((ARRAY['babysitter'::character varying, 'caregiver for elderly'::character varying, 'playmate for children'::character varying])::text[])))
);


ALTER TABLE public.job OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 29481)
-- Name: job_application; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.job_application (
    caregiver_user_id integer NOT NULL,
    job_id integer NOT NULL,
    date_applied date DEFAULT CURRENT_DATE NOT NULL
);


ALTER TABLE public.job_application OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 29434)
-- Name: member; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.member (
    member_user_id integer NOT NULL,
    house_rules text,
    dependent_description text
);


ALTER TABLE public.member OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 29401)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    email character varying(255) NOT NULL,
    given_name character varying(50) NOT NULL,
    surname character varying(50) NOT NULL,
    city character varying(100),
    phone_number character varying(20) NOT NULL,
    profile_description text,
    password character varying(255) NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 29527)
-- Name: job_applications_view; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.job_applications_view AS
 SELECT ja.job_id,
    j.required_caregiving_type,
    j.other_requirements,
    j.date_posted,
    (((m_user.given_name)::text || ' '::text) || (m_user.surname)::text) AS job_poster_name,
    ja.caregiver_user_id,
    (((cg_user.given_name)::text || ' '::text) || (cg_user.surname)::text) AS applicant_name,
    c.caregiving_type,
    c.hourly_rate,
    ja.date_applied
   FROM (((((public.job_application ja
     JOIN public.job j ON ((ja.job_id = j.job_id)))
     JOIN public.member m ON ((j.member_user_id = m.member_user_id)))
     JOIN public.users m_user ON ((m.member_user_id = m_user.user_id)))
     JOIN public.caregiver c ON ((ja.caregiver_user_id = c.caregiver_user_id)))
     JOIN public.users cg_user ON ((c.caregiver_user_id = cg_user.user_id)));


ALTER VIEW public.job_applications_view OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 29461)
-- Name: job_job_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.job_job_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.job_job_id_seq OWNER TO postgres;

--
-- TOC entry 5087 (class 0 OID 0)
-- Dependencies: 224
-- Name: job_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.job_job_id_seq OWNED BY public.job.job_id;


--
-- TOC entry 219 (class 1259 OID 29400)
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- TOC entry 5088 (class 0 OID 0)
-- Dependencies: 219
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- TOC entry 4890 (class 2604 OID 29504)
-- Name: appointment appointment_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment ALTER COLUMN appointment_id SET DEFAULT nextval('public.appointment_appointment_id_seq'::regclass);


--
-- TOC entry 4887 (class 2604 OID 29465)
-- Name: job job_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job ALTER COLUMN job_id SET DEFAULT nextval('public.job_job_id_seq'::regclass);


--
-- TOC entry 4886 (class 2604 OID 29404)
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- TOC entry 5075 (class 0 OID 29447)
-- Dependencies: 223
-- Data for Name: address; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.address (member_user_id, house_number, street, town) FROM stdin;
3	25	Abai	Astana
4	5	Satpayev	Almaty
6	7	Saryarka	Astana
7	19	Abai	Astana
8	3	Turan	Astana
9	8	Al-Farabi	Almaty
10	30	Saryarka	Astana
\.


--
-- TOC entry 5080 (class 0 OID 29501)
-- Dependencies: 228
-- Data for Name: appointment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.appointment (appointment_id, caregiver_user_id, member_user_id, appointment_date, appointment_time, work_hours, status) FROM stdin;
1	3	3	2025-02-05	09:00:00	4.0	accepted
4	6	6	2025-02-08	14:00:00	2.5	pending
5	7	7	2025-02-09	08:00:00	6.0	accepted
6	8	8	2025-02-10	19:00:00	4.0	declined
7	9	9	2025-02-11	13:00:00	3.0	accepted
10	10	10	2025-02-14	17:00:00	5.5	accepted
\.


--
-- TOC entry 5073 (class 0 OID 29419)
-- Dependencies: 221
-- Data for Name: caregiver; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.caregiver (caregiver_user_id, photo, gender, caregiving_type, hourly_rate) FROM stdin;
1	arman.jpg	Male	caregiver for elderly	13.20
2	amina.jpg	Female	babysitter	9.80
3	bota.jpg	Female	caregiver for elderly	16.50
4	daniyar.jpg	Male	babysitter	8.30
5	saltanat.jpg	Female	caregiver for elderly	12.10
6	ivan.jpg	Male	babysitter	11.00
7	aliya.jpg	Female	playmate for children	17.60
8	john.jpg	Male	babysitter	7.80
9	mary.jpg	Female	babysitter	14.30
10	timur.jpg	Male	caregiver for elderly	11.55
\.


--
-- TOC entry 5077 (class 0 OID 29462)
-- Dependencies: 225
-- Data for Name: job; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.job (job_id, member_user_id, required_caregiving_type, other_requirements, date_posted) FROM stdin;
2	3	caregiver for elderly	Soft-spoken and experienced with dementia care.	2025-01-12
5	6	babysitter	Soft-spoken, can drive children to activities and help with homework.	2025-01-20
6	7	playmate for children	Experience with autism, very soft-spoken and structured.	2025-01-22
7	8	babysitter	Comfortable with pets; flexible evening hours.	2025-01-24
8	9	babysitter	Can manage twins, calm under pressure.	2025-01-26
9	10	caregiver for elderly	Night shifts, responsible, basic first-aid knowledge.	2025-01-28
10	3	caregiver for elderly	Soft-spoken, can track medications and accompany to clinics.	2025-02-01
\.


--
-- TOC entry 5078 (class 0 OID 29481)
-- Dependencies: 226
-- Data for Name: job_application; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.job_application (caregiver_user_id, job_id, date_applied) FROM stdin;
1	2	2025-01-13
3	2	2025-01-14
7	6	2025-01-23
8	5	2025-01-21
9	5	2025-01-21
2	7	2025-01-25
4	7	2025-01-25
3	9	2025-01-29
10	9	2025-01-29
6	8	2025-01-27
\.


--
-- TOC entry 5074 (class 0 OID 29434)
-- Dependencies: 222
-- Data for Name: member; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.member (member_user_id, house_rules, dependent_description) FROM stdin;
3	No pets. No smoking.	Elderly mother with dementia.
4	No alcohol allowed.	Younger brother needing tutoring and supervision.
6	No shoes inside.	Two kids aged 5 and 8.
7	No pets. Quiet home.	Child with autism requiring routine.
8	No smoking. Pets allowed.	Infant care needed in the evenings.
9	No loud music after 20:00.	Newborn twins requiring night care.
10	No pets. No smoking; quiet neighborhood.	Grandparents requiring daily assistance.
\.


--
-- TOC entry 5072 (class 0 OID 29401)
-- Dependencies: 220
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, email, given_name, surname, city, phone_number, profile_description, password) FROM stdin;
2	amina.aminova@example.com	Amina	Aminova	Astana	+77772345678	Mother of two looking for help.	pass2
3	bota.baimen@example.com	Bota	Baimen	Astana	+77773456789	Professional nurse.	pass3
4	daniyar.duisen@example.com	Daniyar	Duisen	Almaty	+77774567890	Student offering babysitting.	pass4
5	saltanat.serik@example.com	Saltanat	Serik	Astana	+77775678901	Needs help caring for grandmother.	pass5
6	ivan.ivanov@example.com	Ivan	Ivanov	Astana	+77776789012	Part-time caregiver.	pass6
7	aliya.akhmet@example.com	Aliya	Akhmet	Astana	+77777890123	Special needs care experience.	pass7
8	john.doe@example.com	John	Doe	Shymkent	+77778901234	Babysitter with flexible schedule.	pass8
9	mary.jane@example.com	Mary	Jane	Astana	+77779012345	Nurse and babysitter.	pass9
10	timur.tolegen@example.com	Timur	Tolegen	Almaty	+77770123456	Looking for caregiver for grandparents.	pass10
1	arman.armanov@example.com	Arman	Armanov	Astana	+77773414141	Experienced caregiver and IT student.	pass1
\.


--
-- TOC entry 5089 (class 0 OID 0)
-- Dependencies: 227
-- Name: appointment_appointment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.appointment_appointment_id_seq', 1, false);


--
-- TOC entry 5090 (class 0 OID 0)
-- Dependencies: 224
-- Name: job_job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.job_job_id_seq', 1, false);


--
-- TOC entry 5091 (class 0 OID 0)
-- Dependencies: 219
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 1, false);


--
-- TOC entry 4908 (class 2606 OID 29455)
-- Name: address address_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.address
    ADD CONSTRAINT address_pkey PRIMARY KEY (member_user_id);


--
-- TOC entry 4914 (class 2606 OID 29516)
-- Name: appointment appointment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment
    ADD CONSTRAINT appointment_pkey PRIMARY KEY (appointment_id);


--
-- TOC entry 4904 (class 2606 OID 29428)
-- Name: caregiver caregiver_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.caregiver
    ADD CONSTRAINT caregiver_pkey PRIMARY KEY (caregiver_user_id);


--
-- TOC entry 4912 (class 2606 OID 29489)
-- Name: job_application job_application_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_application
    ADD CONSTRAINT job_application_pkey PRIMARY KEY (caregiver_user_id, job_id);


--
-- TOC entry 4910 (class 2606 OID 29475)
-- Name: job job_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job
    ADD CONSTRAINT job_pkey PRIMARY KEY (job_id);


--
-- TOC entry 4906 (class 2606 OID 29441)
-- Name: member member_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member
    ADD CONSTRAINT member_pkey PRIMARY KEY (member_user_id);


--
-- TOC entry 4898 (class 2606 OID 29416)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4900 (class 2606 OID 29418)
-- Name: users users_phone_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_phone_number_key UNIQUE (phone_number);


--
-- TOC entry 4902 (class 2606 OID 29414)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4917 (class 2606 OID 29456)
-- Name: address fk_address_member; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.address
    ADD CONSTRAINT fk_address_member FOREIGN KEY (member_user_id) REFERENCES public.member(member_user_id) ON DELETE CASCADE;


--
-- TOC entry 4921 (class 2606 OID 29517)
-- Name: appointment fk_appointment_caregiver; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment
    ADD CONSTRAINT fk_appointment_caregiver FOREIGN KEY (caregiver_user_id) REFERENCES public.caregiver(caregiver_user_id) ON DELETE CASCADE;


--
-- TOC entry 4922 (class 2606 OID 29522)
-- Name: appointment fk_appointment_member; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointment
    ADD CONSTRAINT fk_appointment_member FOREIGN KEY (member_user_id) REFERENCES public.member(member_user_id) ON DELETE CASCADE;


--
-- TOC entry 4915 (class 2606 OID 29429)
-- Name: caregiver fk_caregiver_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.caregiver
    ADD CONSTRAINT fk_caregiver_user FOREIGN KEY (caregiver_user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- TOC entry 4918 (class 2606 OID 29476)
-- Name: job fk_job_member; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job
    ADD CONSTRAINT fk_job_member FOREIGN KEY (member_user_id) REFERENCES public.member(member_user_id) ON DELETE CASCADE;


--
-- TOC entry 4919 (class 2606 OID 29490)
-- Name: job_application fk_jobapp_caregiver; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_application
    ADD CONSTRAINT fk_jobapp_caregiver FOREIGN KEY (caregiver_user_id) REFERENCES public.caregiver(caregiver_user_id) ON DELETE CASCADE;


--
-- TOC entry 4920 (class 2606 OID 29495)
-- Name: job_application fk_jobapp_job; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_application
    ADD CONSTRAINT fk_jobapp_job FOREIGN KEY (job_id) REFERENCES public.job(job_id) ON DELETE CASCADE;


--
-- TOC entry 4916 (class 2606 OID 29442)
-- Name: member fk_member_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.member
    ADD CONSTRAINT fk_member_user FOREIGN KEY (member_user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


-- Completed on 2025-11-24 23:36:48

--
-- PostgreSQL database dump complete
--

\unrestrict ocEQQs2ul5eMu4zgrjW5YcXbA92kWcxzMLwlVB1zBHpcNv0bdwHpchlHdNucNO2

