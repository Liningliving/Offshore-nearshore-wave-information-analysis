import java.nio.file.*;
import java.io.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;

/** Zero lag only, no significance or sensitivity calculations. Input: hours,Ho,Hn,Tp,Dx,Dy. */
public final class PrimaryInformationMeasures {
  public static void main(String[] args)throws Exception{
    List<String> rows=Files.readAllLines(Path.of(args[0]));int n=rows.size();
    int[] hours=new int[n];double[][] ho=new double[n][1],hn=new double[n][1],tp=new double[n][1],dir=new double[n][2];
    for(int i=0;i<n;i++){String[] f=rows.get(i).split(",");hours[i]=Integer.parseInt(f[0]);ho[i][0]=Double.parseDouble(f[1]);hn[i][0]=Double.parseDouble(f[2]);tp[i][0]=Double.parseDouble(f[3]);dir[i][0]=Double.parseDouble(f[4]);dir[i][1]=Double.parseDouble(f[5]);}
    MutualInfoCalculatorMultiVariateKraskov1 mi=new MutualInfoCalculatorMultiVariateKraskov1();SharedEstimatorSettings.apply(mi);ElapsedHourLoader.load(mi,hours,ho,hn,4,45);SharedEstimatorSettings.verify(mi);
    ConditionalMutualInfoCalculatorMultiVariateKraskov1 period=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();SharedEstimatorSettings.apply(period);ElapsedHourLoader.load(period,hours,tp,hn,ho,4,45);SharedEstimatorSettings.verify(period);
    ConditionalMutualInfoCalculatorMultiVariateKraskov1 direction=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();SharedEstimatorSettings.apply(direction);ElapsedHourLoader.load(direction,hours,dir,hn,ho,4,45);SharedEstimatorSettings.verify(direction);
    try(PrintWriter out=new PrintWriter(args[1]);PrintWriter times=new PrintWriter(args[2])){
      out.println("measure,sample_size,x_dimensions,y_dimensions,condition_dimensions,nats,bits,k,NORMALISE,NORM_TYPE,DYN_CORR_EXCL,USE_GPU,noise_std,noise_seed,threads");
      emit(out,"I(Ho;Hn)",n,1,0,mi.computeAverageLocalOfObservations());
      emit(out,"I(Tp_o;Hn|Ho)",n,1,1,period.computeAverageLocalOfObservations());
      emit(out,"I((Dx Dy);Hn|Ho)",n,2,1,direction.computeAverageLocalOfObservations());
      times.println("row,expected_elapsed_hour,mi_time,period_time,direction_time,mi_set,period_set,direction_set");
      for(int i=0;i<n;i++)times.println(i+","+hours[i]+","+mi.getObservationTimePoints()[i]+","+period.getObservationTimePoints()[i]+","+direction.getObservationTimePoints()[i]+","+mi.getObservationSetIndices()[i]+","+period.getObservationSetIndices()[i]+","+direction.getObservationSetIndices()[i]);
    }
  }
  static void emit(PrintWriter out,String measure,int n,int dx,int dz,double value){
    if(!Double.isFinite(value))throw new IllegalStateException("Nonfinite estimate");
    out.printf(Locale.ROOT,"%s,%d,%d,1,%d,%.17g,%.17g,4,true,MAX_NORM,45,false,1e-8,20261031,1%n",measure,n,dx,dz,value,value/Math.log(2));
  }
}
