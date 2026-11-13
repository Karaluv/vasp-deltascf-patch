      IF(SADDLE_MODE/=0) THEN
         CALL NTO_SADDLE_MEASURE(W,W_F,WDES,LATT_CUR,CQIJ,LMDIM,IO,NTO_N,BSTEP,EFERMI,SADDLE_TRY,SADDLE_MAXTRY)
         IF(.NOT.SADDLE_RELAXED.AND.ABS(SADDLE_ACTUAL-SADDLE_A_OUT)>MAX(1E-6_q,0.01_q*ABS(SADDLE_A_OUT))) THEN
            IF(SADDLE_TRY>=SADDLE_MAXTRY) CALL vtutor%error('NTO_SADDLE: finite retraction correction failed')
            CALL NTO_SADDLE_RETRY(W,W_F,WDES,CHF,IO,NTO_N)
            CYCLE saddle_trial
         ENDIF
      ENDIF
      EXIT saddle_trial
      ENDDO saddle_trial
