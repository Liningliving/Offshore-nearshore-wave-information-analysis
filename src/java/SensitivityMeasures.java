import java.nio.file.*;
import java.io.*;
import java.util.*;
import infodynamics.measures.continuous.kraskov.*;

/** Input: elapsed tick, Ho(t), Hn(t+lag), Tp(t), Dx(t), Dy(t). */
public final class SensitivityMeasures {
  public static void main(String[] args)throws Exception{
    int k=Integer.parseInt(args[3]);double window=Double.parseDouble(args[4]),unit=Double.parseDouble(args[5]);int ticks=SensitivitySettings.windowTicks(window,unit);
    List<String> rows=Files.readAllLines(Path.of(args[0]));int n=rows.size();int[] times=new int[n];
    double[][] ho=new double[n][1],hn=new double[n][1],tp=new double[n][1],dir=new double[n][2];
    for(int i=0;i<n;i++){String[] f=rows.get(i).split(",");times[i]=Integer.parseInt(f[0]);ho[i][0]=Double.parseDouble(f[1]);hn[i][0]=Double.parseDouble(f[2]);tp[i][0]=Double.parseDouble(f[3]);dir[i][0]=Double.parseDouble(f[4]);dir[i][1]=Double.parseDouble(f[5]);}
    MutualInfoCalculatorMultiVariateKraskov1 mi=new MutualInfoCalculatorMultiVariateKraskov1();SharedEstimatorSettings.apply(mi);ElapsedHourLoader.load(mi,times,ho,hn,k,ticks);SensitivitySettings.verify(mi,k,ticks);
    ConditionalMutualInfoCalculatorMultiVariateKraskov1 period=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();SharedEstimatorSettings.apply(period);ElapsedHourLoader.load(period,times,tp,hn,ho,k,ticks);SensitivitySettings.verify(period,k,ticks);
    ConditionalMutualInfoCalculatorMultiVariateKraskov1 direction=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();SharedEstimatorSettings.apply(direction);ElapsedHourLoader.load(direction,times,dir,hn,ho,k,ticks);SensitivitySettings.verify(direction,k,ticks);
    try(PrintWriter out=new PrintWriter(args[1]);PrintWriter audit=new PrintWriter(args[2])){
      out.println("measure,sample_size,x_dimensions,y_dimensions,condition_dimensions,k,theiler_hours,theiler_ticks,index_unit_hours,nats,bits");
      emit(out,"height_mi",n,1,0,k,window,ticks,unit,mi.computeAverageLocalOfObservations());
      emit(out,"period_cmi",n,1,1,k,window,ticks,unit,period.computeAverageLocalOfObservations());
      emit(out,"direction_cmi",n,2,1,k,window,ticks,unit,direction.computeAverageLocalOfObservations());
      audit.println("row,expected_tick,mi_tick,period_tick,direction_tick,mi_set,period_set,direction_set");
      for(int i=0;i<n;i++)audit.println(i+","+times[i]+","+mi.getObservationTimePoints()[i]+","+period.getObservationTimePoints()[i]+","+direction.getObservationTimePoints()[i]+","+mi.getObservationSetIndices()[i]+","+period.getObservationSetIndices()[i]+","+direction.getObservationSetIndices()[i]);
    }
  }
  static void emit(PrintWriter out,String m,int n,int dx,int dz,int k,double w,int ticks,double unit,double value){
    if(!Double.isFinite(value))throw new IllegalStateException("Nonfinite estimate");
    out.printf(Locale.ROOT,"%s,%d,%d,1,%d,%d,%.1f,%d,%.1f,%.17g,%.17g%n",m,n,dx,dz,k,w,ticks,unit,value,value/Math.log(2));
  }
}
