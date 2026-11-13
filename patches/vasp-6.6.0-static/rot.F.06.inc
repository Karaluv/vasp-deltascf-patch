      ! Full PAW S-norm of the *raw* EDWAV gradient outside the 224-band
      ! subspace, before preconditioning. This is an external-gradient
      ! estimate, not asserted to be the exact dual-metric QFP norm.
      IF(SADDLE_EXT_REQUESTED.AND.ISP==2.AND.N<=191.AND.IFLAG/=2) THEN
         DO ISPINOR=0,WDES1%NRSPINORS-1
            CALL FFTWAV(NGVECTOR,WDES1%NINDPW(1),WSEARCH%CR(1+ISPINOR*WDES1%GRID%MPLWV), &
                 WSEARCH%CW(1+ISPINOR*NGVECTOR),GRID)
         ENDDO
         IF(LREAL) THEN
#ifdef OFFLOADING
           IF(OFFLOAD_ON) THEN
              CALL RPRO1_ACC(NONLR_S,WDES1,WSEARCH)
           ELSE
#endif
              CALL RPRO1(NONLR_S,WDES1,WSEARCH)
#ifdef OFFLOADING
           ENDIF
#endif
         ELSE
           CALL PROJ1(NONL_S,WDES1,WSEARCH)
         ENDIF
         CALL CNORMA(WSEARCH,CQIJ,ISP,SADDLE_RAW_SCALE)
         IF(ieee_is_nan(SADDLE_RAW_SCALE)) THEN
            CALL vtutor%error('NTO_SADDLE: nonfinite PAW raw-gradient norm')
         ELSE IF(.NOT.ieee_is_finite(SADDLE_RAW_SCALE)) THEN
            ! CNORMA returns an infinite inverse norm for an exactly zero vector.
         ELSE IF(SADDLE_RAW_SCALE>0._q) THEN
            SADDLE_RAW_EXT2=SADDLE_RAW_EXT2+1._q/SADDLE_RAW_SCALE**2
         ELSE
            CALL vtutor%error('NTO_SADDLE: invalid PAW raw-gradient norm')
         ENDIF
         ! Restore the unpreconditioned vector exactly before the stock path.
         CALL WZCOPY(WDES%NRPLWV,CF(1,NP),1,WSEARCH%CW(1),1)
      ENDIF

